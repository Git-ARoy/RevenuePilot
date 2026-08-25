import uuid
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import ActionType, DiagnosisCode
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.agent_decision import AgentDecision
from app.policies.policy_engine import PolicyEngine

@dataclass
class StrategyDecision:
    action_type: ActionType
    reason_code: str
    confidence: float

class StrategyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.policy_engine = PolicyEngine(db)

    async def select_strategy(self, case: RecoveryCase, payment: Payment, score: float) -> StrategyDecision:
        policy = await self.policy_engine.get_policy(case.merchant_id)
        
        decision = StrategyDecision(ActionType.ESCALATE_TO_HUMAN, "DEFAULT_FALLBACK", 1.0)
        
        if case.diagnosis_code in [DiagnosisCode.NON_RECOVERABLE, DiagnosisCode.ALREADY_RECOVERED]:
            decision = StrategyDecision(ActionType.STOP_RECOVERY, "TERMINAL_DIAGNOSIS", 1.0)
        elif score < 0.15:
            decision = StrategyDecision(ActionType.ESCALATE_TO_HUMAN, "LOW_CONFIDENCE_SCORE", 1.0)
        elif case.amount_at_risk > policy.human_approval_threshold:
            decision = StrategyDecision(ActionType.ESCALATE_TO_HUMAN, "AMOUNT_EXCEEDS_THRESHOLD", 1.0)
        elif case.diagnosis_code == DiagnosisCode.TRANSIENT_GATEWAY_FAILURE and score > 0.6:
            if case.attempt_count == 0:
                decision = StrategyDecision(ActionType.RETRY_PAYMENT, "TRANSIENT_FIRST_ATTEMPT", score)
            else:
                decision = StrategyDecision(ActionType.SCHEDULE_RETRY, "TRANSIENT_RETRY", score)
        elif case.diagnosis_code in [DiagnosisCode.CUSTOMER_ACTION_REQUIRED, DiagnosisCode.PAYMENT_METHOD_FAILURE, DiagnosisCode.EXPIRED_PAYMENT_METHOD]:
            decision = StrategyDecision(ActionType.CREATE_PAYMENT_LINK, "NEW_PAYMENT_METHOD_REQUIRED", score)
        elif case.diagnosis_code == DiagnosisCode.INSUFFICIENT_FUNDS and case.attempt_count < 2:
            decision = StrategyDecision(ActionType.SCHEDULE_RETRY, "INSUFFICIENT_FUNDS_RETRY", score)
        elif case.diagnosis_code == DiagnosisCode.BANK_DECLINE:
            if case.attempt_count == 0:
                decision = StrategyDecision(ActionType.CREATE_PAYMENT_LINK, "BANK_DECLINE_NEW_METHOD", score)
            else:
                decision = StrategyDecision(ActionType.ESCALATE_TO_HUMAN, "BANK_DECLINE_ESCALATE", score)
        elif case.diagnosis_code == DiagnosisCode.UNKNOWN_PAYMENT_FAILURE:
            if score > 0.5:
                decision = StrategyDecision(ActionType.CREATE_PAYMENT_LINK, "UNKNOWN_TRY_LINK", score)
            else:
                decision = StrategyDecision(ActionType.ESCALATE_TO_HUMAN, "UNKNOWN_ESCALATE", score)

        # Audit decision
        agent_dec = AgentDecision(
            recovery_case_id=case.id,
            stage="strategy_selection",
            decision=decision.action_type.value,
            reason_code=decision.reason_code,
            confidence=decision.confidence
        )
        self.db.add(agent_dec)
        await self.db.flush()
        
        return decision
