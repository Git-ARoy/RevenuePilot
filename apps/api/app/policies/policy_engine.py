import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import ActionType, CaseStatus, AttemptStatus, AuditEventType, ActorType
from app.models.recovery_case import RecoveryCase
from app.models.policy_config import PolicyConfig
from app.models.recovery_attempt import RecoveryAttempt
from app.models.audit_event import AuditEvent

@dataclass
class PolicyCheck:
    rule: str
    passed: bool
    detail: str

@dataclass
class PolicyDecision:
    allowed: bool
    checks: List[PolicyCheck]
    block_reason: Optional[str] = None

class PolicyEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_policy(self, merchant_id: uuid.UUID) -> PolicyConfig:
        stmt = select(PolicyConfig).where(PolicyConfig.merchant_id == merchant_id)
        result = await self.db.execute(stmt)
        policy = result.scalar_one_or_none()
        if not policy:
            policy = PolicyConfig(
                merchant_id=merchant_id,
                allowed_actions=[a.value for a in ActionType]
            )
            self.db.add(policy)
            await self.db.flush()
        return policy

    async def evaluate(self, case: RecoveryCase, proposed_action: ActionType) -> PolicyDecision:
        policy = await self.get_policy(case.merchant_id)
        checks = []
        
        # 1. CASE_NOT_TERMINAL
        terminal_statuses = [CaseStatus.RECOVERED, CaseStatus.UNRECOVERED, CaseStatus.STOPPED, CaseStatus.TERMINAL]
        passed = case.status not in terminal_statuses
        checks.append(PolicyCheck("CASE_NOT_TERMINAL", passed, f"Case status is {case.status.value}"))

        # 2. MAX_ATTEMPTS
        passed = case.attempt_count < policy.max_attempts
        checks.append(PolicyCheck("MAX_ATTEMPTS", passed, f"Attempt count {case.attempt_count} / {policy.max_attempts}"))

        # 3. AMOUNT_LIMIT
        passed = case.amount_at_risk <= policy.max_automated_recovery_amount
        checks.append(PolicyCheck("AMOUNT_LIMIT", passed, f"Amount {case.amount_at_risk} <= {policy.max_automated_recovery_amount}"))

        # 4. COOLDOWN
        passed = True
        if case.next_eligible_at and case.next_eligible_at > datetime.now(timezone.utc):
            passed = False
        checks.append(PolicyCheck("COOLDOWN", passed, f"Next eligible at {case.next_eligible_at}"))

        # 5. ACTION_ALLOWED
        passed = proposed_action.value in policy.allowed_actions
        checks.append(PolicyCheck("ACTION_ALLOWED", passed, f"Action {proposed_action.value} allowed"))

        # 6. NO_CONCURRENT_ACTION
        stmt = select(RecoveryAttempt).where(and_(
            RecoveryAttempt.recovery_case_id == case.id,
            RecoveryAttempt.status.in_([AttemptStatus.PENDING, AttemptStatus.EXECUTING])
        ))
        res = await self.db.execute(stmt)
        passed = res.scalar_one_or_none() is None
        checks.append(PolicyCheck("NO_CONCURRENT_ACTION", passed, "No pending/executing attempts"))

        # 7. HUMAN_APPROVAL
        if proposed_action != ActionType.ESCALATE_TO_HUMAN:
            passed = case.amount_at_risk < policy.human_approval_threshold
            checks.append(PolicyCheck("HUMAN_APPROVAL", passed, f"Amount {case.amount_at_risk} < {policy.human_approval_threshold}"))

        allowed = all(c.passed for c in checks)
        block_reason = next((f"{c.rule}: {c.detail}" for c in checks if not c.passed), None)

        if not allowed:
            audit = AuditEvent(
                recovery_case_id=case.id,
                event_type=AuditEventType.ACTION_BLOCKED,
                actor_type=ActorType.SYSTEM,
                metadata_={"proposed_action": proposed_action.value, "block_reason": block_reason}
            )
            self.db.add(audit)
            await self.db.flush()

        return PolicyDecision(allowed=allowed, checks=checks, block_reason=block_reason)
