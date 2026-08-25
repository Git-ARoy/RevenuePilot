import uuid
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import CaseStatus, ActionType, AuditEventType, ActorType
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.audit_event import AuditEvent
from app.services.case_service import CaseService
from app.services.diagnosis_service import DiagnosisService
from app.services.scoring_service import RuleBasedRecoveryScorer
from app.policies.policy_engine import PolicyEngine
from app.services.strategy_service import StrategyService
from app.integrations.tool_gateway import ToolGateway, ToolRequest, ToolResponse

logger = logging.getLogger(__name__)

class RecoveryOrchestrator:
    def __init__(self, db: AsyncSession, llm_provider=None, adapter=None):
        self.db = db
        self.case_service = CaseService(db)
        self.diagnosis_service = DiagnosisService(db, llm_provider)
        self.scorer = RuleBasedRecoveryScorer()
        self.policy_engine = PolicyEngine(db)
        self.strategy_service = StrategyService(db)
        self.tool_gateway = ToolGateway(db, adapter=adapter)

    async def _audit(self, case: RecoveryCase, event_type: AuditEventType, metadata: dict = None):
        audit = AuditEvent(
            recovery_case_id=case.id,
            event_type=event_type,
            actor_type=ActorType.SYSTEM,
            metadata_=metadata or {}
        )
        self.db.add(audit)
        await self.db.flush()

    async def process_case(self, case_id: uuid.UUID, action_type: ActionType = None, reason_code: str = None, idempotency_key: str = None) -> RecoveryCase:
        case = await self.case_service.get_case(case_id)
        if not case:
            return None

        try:
            payment = (await self.db.execute(select(Payment).where(Payment.id == case.payment_id))).scalar_one_or_none()

            if case.status == CaseStatus.DETECTED:
                diagnosis = await self.diagnosis_service.diagnose(case, payment)
                case.status = CaseStatus.DIAGNOSED
                await self._audit(case, AuditEventType.CASE_DIAGNOSED, {"code": diagnosis.code.value})
                await self.db.commit()

            if case.status == CaseStatus.DIAGNOSED:
                score, factors = self.scorer.score(case, payment)
                case.recovery_score = score
                case.status = CaseStatus.ELIGIBILITY_CHECKED
                await self.db.commit()

            if case.status == CaseStatus.ELIGIBILITY_CHECKED:
                if action_type:
                    case.current_strategy = action_type
                else:
                    strategy = await self.strategy_service.select_strategy(case, payment, case.recovery_score)
                    case.current_strategy = strategy.action_type
                case.status = CaseStatus.STRATEGY_SELECTED
                await self._audit(case, AuditEventType.ACTION_PROPOSED, {"action": case.current_strategy.value})
                await self.db.commit()
            
            if case.status == CaseStatus.STRATEGY_SELECTED:
                if case.current_strategy == ActionType.STOP_RECOVERY:
                    case.status = CaseStatus.STOPPED
                    case.terminal_reason = "Recovery stopped by strategy"
                    await self._audit(case, AuditEventType.CASE_STOPPED, {"reason": "Stopped by strategy"})
                elif case.current_strategy == ActionType.ESCALATE_TO_HUMAN:
                    case.status = CaseStatus.ESCALATED
                    case.terminal_reason = reason_code or "Escalated to human by strategy"
                    await self._audit(case, AuditEventType.CASE_ESCALATED, {"reason": case.terminal_reason})
                else:
                    decision = await self.policy_engine.evaluate(case, case.current_strategy)
                    if decision.allowed:
                        case.status = CaseStatus.ACTION_PENDING
                    else:
                        case.status = CaseStatus.BLOCKED
                        case.terminal_reason = decision.block_reason
                        await self._audit(case, AuditEventType.ACTION_BLOCKED, {"reason": decision.block_reason})
                await self.db.commit()
            
            if case.status == CaseStatus.ACTION_PENDING:
                key = idempotency_key or f"auto_{case.id}_{case.attempt_count + 1}"
                req = ToolRequest(
                    case_id=case.id,
                    action_type=case.current_strategy,
                    idempotency_key=key,
                    parameters={}
                )
                tool_resp = await self.tool_gateway.execute(req, case)
                if not tool_resp.success:
                    if case.attempt_count < case.max_attempts and tool_resp.retryable:
                        case.status = CaseStatus.RETRY_PENDING
                    else:
                        case.status = CaseStatus.ESCALATED
                        case.terminal_reason = tool_resp.error_message or "Execution failed"
                        await self._audit(case, AuditEventType.CASE_ESCALATED, {"reason": case.terminal_reason})
                await self.db.commit()

        except Exception as e:
            logger.exception("Error in process_case")
            case.status = CaseStatus.ESCALATED
            case.terminal_reason = str(e)
            await self._audit(case, AuditEventType.CASE_ESCALATED, {"error": str(e)})
            await self.db.commit()

        await self.db.refresh(case)
        return case

    async def process_batch(self, batch_id: uuid.UUID) -> dict:
        cases = (await self.db.execute(select(RecoveryCase).where(RecoveryCase.batch_id == batch_id))).scalars().all()
        processed = 0
        for case in cases:
            await self.process_case(case.id)
            processed += 1
        return {"batch_id": str(batch_id), "processed": processed}
