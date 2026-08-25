"""
Outcome Simulator — Simulates webhook-like payment events for recovery actions.

After the agent takes an action (e.g., creates a payment link),
this service simulates whether the customer actually pays.

Success rates vary by diagnosis code to produce realistic metrics.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    CaseStatus, AttemptStatus, AuditEventType, ActorType, DiagnosisCode
)
from app.models.recovery_case import RecoveryCase
from app.models.recovery_attempt import RecoveryAttempt
from app.models.audit_event import AuditEvent


class OutcomeSimulator:
    """
    Simulates payment outcomes for cases waiting for verification.
    
    This replaces the webhook-driven verification that would happen
    in production. It uses deterministic random to decide whether
    a recovery action resulted in actual payment.
    """

    # Recovery success rates by diagnosis (after action was taken)
    OUTCOME_RATES = {
        DiagnosisCode.TRANSIENT_GATEWAY_FAILURE: 0.78,
        DiagnosisCode.CUSTOMER_ACTION_REQUIRED: 0.50,
        DiagnosisCode.PAYMENT_METHOD_FAILURE: 0.32,
        DiagnosisCode.INSUFFICIENT_FUNDS: 0.22,
        DiagnosisCode.EXPIRED_PAYMENT_METHOD: 0.18,
        DiagnosisCode.BANK_DECLINE: 0.28,
        DiagnosisCode.UNKNOWN_PAYMENT_FAILURE: 0.38,
        DiagnosisCode.NON_RECOVERABLE: 0.0,
        DiagnosisCode.ALREADY_RECOVERED: 1.0,
    }

    def __init__(self, db: AsyncSession, seed: int = 42):
        import random
        self.db = db
        self.rng = random.Random(seed + 1000)  # Different seed from adapter

    async def resolve_pending_outcomes(self, batch_id: uuid.UUID) -> int:
        """
        Resolve all WAITING_FOR_OUTCOME cases in a batch.
        
        Returns the number of cases resolved.
        """
        # Find all cases waiting for outcome in this batch
        result = await self.db.execute(
            select(RecoveryCase).where(
                and_(
                    RecoveryCase.batch_id == batch_id,
                    RecoveryCase.status == CaseStatus.WAITING_FOR_OUTCOME,
                )
            )
        )
        cases = list(result.scalars().all())

        resolved = 0
        for case in cases:
            await self._resolve_case(case)
            resolved += 1

        await self.db.flush()
        return resolved

    async def _resolve_case(self, case: RecoveryCase) -> None:
        """Simulate outcome for a single case."""
        rate = self.OUTCOME_RATES.get(case.diagnosis_code, 0.35)

        # Check if the simulation adapter flagged this as will_be_paid
        # (from the tool response data)
        last_attempt = await self._get_last_attempt(case.id)
        if last_attempt and last_attempt.tool_response:
            will_be_paid = last_attempt.tool_response.get("data", {}).get(
                "will_be_paid"
            )
            if will_be_paid is not None:
                recovered = will_be_paid
            else:
                recovered = self.rng.random() < rate
        else:
            recovered = self.rng.random() < rate

        if recovered:
            case.status = CaseStatus.RECOVERED
            case.amount_recovered = case.amount_at_risk
            case.terminal_reason = "Payment received after recovery action"

            audit_event_type = AuditEventType.RECOVERY_VERIFIED
            metadata = {
                "amount_recovered": case.amount_at_risk,
                "recovery_source": "simulation",
                "simulated_event": "payment.captured",
            }
        else:
            case.status = CaseStatus.UNRECOVERED
            case.terminal_reason = "Payment not received within simulation window"

            audit_event_type = AuditEventType.CASE_STOPPED
            metadata = {
                "reason": "no_payment_received",
                "recovery_source": "simulation",
            }

        case.updated_at = datetime.now(timezone.utc)

        # Create audit event
        audit = AuditEvent(
            id=uuid.uuid4(),
            recovery_case_id=case.id,
            event_type=audit_event_type,
            actor_type=ActorType.SYSTEM,
            metadata_=metadata,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(audit)

    async def _get_last_attempt(
        self, case_id: uuid.UUID
    ) -> RecoveryAttempt | None:
        """Get the most recent recovery attempt for a case."""
        result = await self.db.execute(
            select(RecoveryAttempt)
            .where(RecoveryAttempt.recovery_case_id == case_id)
            .order_by(RecoveryAttempt.attempt_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
