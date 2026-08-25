import uuid
from dataclasses import dataclass
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recovery_case import RecoveryCase
from app.models.recovery_attempt import RecoveryAttempt
from app.models.enums import CaseStatus, AttemptStatus

@dataclass
class DashboardSummary:
    amount_at_risk: int
    amount_recovered: int
    recovery_rate: float
    active_cases: int
    escalated_cases: int
    failed_actions: int

@dataclass
class BatchMetrics:
    cases: int
    amount_at_risk: int
    amount_recovered: int
    recovery_rate: float
    actions_attempted: int
    escalations: int
    terminal_failures: int

class MetricsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_summary(self, merchant_id: uuid.UUID) -> DashboardSummary:
        stmt = select(
            func.sum(RecoveryCase.amount_at_risk),
            func.sum(RecoveryCase.amount_recovered),
            func.count(RecoveryCase.id)
        ).where(RecoveryCase.merchant_id == merchant_id)
        res = (await self.db.execute(stmt)).one()
        amount_risk = res[0] or 0
        amount_rec = res[1] or 0
        
        active_stmt = select(func.count(RecoveryCase.id)).where(RecoveryCase.merchant_id == merchant_id, RecoveryCase.status.notin_([CaseStatus.RECOVERED, CaseStatus.UNRECOVERED, CaseStatus.TERMINAL, CaseStatus.STOPPED]))
        active = (await self.db.execute(active_stmt)).scalar() or 0
        
        esc_stmt = select(func.count(RecoveryCase.id)).where(RecoveryCase.merchant_id == merchant_id, RecoveryCase.status == CaseStatus.ESCALATED)
        esc = (await self.db.execute(esc_stmt)).scalar() or 0
        
        failed_actions_stmt = select(func.count(RecoveryAttempt.id)).join(RecoveryCase).where(RecoveryCase.merchant_id == merchant_id, RecoveryAttempt.status == AttemptStatus.FAILED)
        failed_actions = (await self.db.execute(failed_actions_stmt)).scalar() or 0
        
        rate = (amount_rec / amount_risk) if amount_risk > 0 else 0.0
        
        return DashboardSummary(
            amount_at_risk=amount_risk,
            amount_recovered=amount_rec,
            recovery_rate=rate,
            active_cases=active,
            escalated_cases=esc,
            failed_actions=failed_actions
        )

    async def compute_batch_metrics(self, batch_id: uuid.UUID) -> BatchMetrics:
        stmt = select(
            func.count(RecoveryCase.id),
            func.sum(RecoveryCase.amount_at_risk),
            func.sum(RecoveryCase.amount_recovered)
        ).where(RecoveryCase.batch_id == batch_id)
        res = (await self.db.execute(stmt)).one()
        cases = res[0] or 0
        amount_risk = res[1] or 0
        amount_rec = res[2] or 0
        
        attempts_stmt = select(func.count(RecoveryAttempt.id)).join(RecoveryCase).where(RecoveryCase.batch_id == batch_id)
        attempts = (await self.db.execute(attempts_stmt)).scalar() or 0
        
        esc_stmt = select(func.count(RecoveryCase.id)).where(RecoveryCase.batch_id == batch_id, RecoveryCase.status == CaseStatus.ESCALATED)
        esc = (await self.db.execute(esc_stmt)).scalar() or 0
        
        term_stmt = select(func.count(RecoveryCase.id)).where(RecoveryCase.batch_id == batch_id, RecoveryCase.status == CaseStatus.TERMINAL)
        term = (await self.db.execute(term_stmt)).scalar() or 0
        
        rate = (amount_rec / amount_risk) if amount_risk > 0 else 0.0
        
        return BatchMetrics(
            cases=cases,
            amount_at_risk=amount_risk,
            amount_recovered=amount_rec,
            recovery_rate=rate,
            actions_attempted=attempts,
            escalations=esc,
            terminal_failures=term
        )
