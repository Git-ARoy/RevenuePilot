"""
Recovery Case Service — Detection and case lifecycle management.

Responsible for:
- Detecting revenue-at-risk from payment events
- Creating/updating RecoveryCase records
- Case type classification
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    CaseStatus, CaseType, DiagnosisCode, AuditEventType, ActorType
)
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.audit_event import AuditEvent


# Payment statuses that indicate potential revenue at risk
FAILURE_STATUSES = {"failed"}
RECOVERABLE_STATUSES = {"failed", "created"}  # created = potentially abandoned


class CaseService:
    """Detects revenue at risk and manages recovery case lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_from_payment(self, payment: Payment) -> Optional[RecoveryCase]:
        """
        Evaluate a payment and create a recovery case if revenue is at risk.
        
        Returns the created/updated RecoveryCase or None if no case is warranted.
        """
        # Already recovered payments are not at risk
        if payment.status == "captured":
            return await self._handle_already_recovered(payment)

        # Only failed payments create new cases
        if payment.status not in FAILURE_STATUSES:
            return None

        # Check if a case already exists for this payment
        existing = await self._find_existing_case(payment.id)
        if existing:
            return await self._update_existing_case(existing, payment)

        # Classify the case type
        case_type = self._classify_case_type(payment)

        # Create a new recovery case
        case = RecoveryCase(
            id=uuid.uuid4(),
            merchant_id=payment.merchant_id,
            payment_id=payment.id,
            case_type=case_type,
            amount_at_risk=payment.amount,
            currency=payment.currency or "INR",
            status=CaseStatus.DETECTED,
            attempt_count=0,
            max_attempts=3,
        )
        self.db.add(case)

        # Create audit event
        audit = AuditEvent(
            id=uuid.uuid4(),
            recovery_case_id=case.id,
            event_type=AuditEventType.CASE_DETECTED,
            actor_type=ActorType.SYSTEM,
            metadata_={
                "amount_at_risk": payment.amount,
                "currency": payment.currency or "INR",
                "case_type": case_type.value,
                "payment_status": payment.status,
                "error_code": payment.error_code,
            },
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(audit)

        await self.db.flush()
        return case

    async def detect_batch(
        self, payments: list[Payment]
    ) -> list[RecoveryCase]:
        """Detect recovery cases from a batch of payments."""
        cases = []
        for payment in payments:
            case = await self.detect_from_payment(payment)
            if case:
                cases.append(case)
        return cases

    def _classify_case_type(self, payment: Payment) -> CaseType:
        """Classify what type of recovery case this is."""
        error_code = (payment.error_code or "").upper()
        error_desc = (payment.error_description or "").lower()

        # Check for recurring/subscription failures
        if "subscription" in error_desc or "recurring" in error_desc:
            return CaseType.FAILED_RECURRING

        # Check for abandoned checkout (payment created but never attempted)
        if payment.status == "created":
            return CaseType.ABANDONED_CHECKOUT

        # Default: failed payment
        return CaseType.FAILED_PAYMENT

    async def _find_existing_case(self, payment_id: uuid.UUID) -> Optional[RecoveryCase]:
        """Find an existing active recovery case for a payment."""
        terminal_statuses = {
            CaseStatus.RECOVERED,
            CaseStatus.TERMINAL,
            CaseStatus.STOPPED,
        }
        result = await self.db.execute(
            select(RecoveryCase).where(
                and_(
                    RecoveryCase.payment_id == payment_id,
                    RecoveryCase.status.notin_(
                        [s.value for s in terminal_statuses]
                    ),
                )
            )
        )
        return result.scalar_one_or_none()

    async def _update_existing_case(
        self, case: RecoveryCase, payment: Payment
    ) -> RecoveryCase:
        """Update an existing case with new payment failure info."""
        # If it was a repeated failure, update the case type
        if case.attempt_count > 0:
            case.case_type = CaseType.REPEATED_FAILURE
        case.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return case

    async def _handle_already_recovered(
        self, payment: Payment
    ) -> Optional[RecoveryCase]:
        """Handle a payment that has already been captured."""
        existing = await self._find_existing_case(payment.id)
        if existing and existing.status != CaseStatus.RECOVERED:
            existing.status = CaseStatus.RECOVERED
            existing.amount_recovered = payment.amount
            existing.terminal_reason = "Payment captured directly"
            existing.updated_at = datetime.now(timezone.utc)

            audit = AuditEvent(
                id=uuid.uuid4(),
                recovery_case_id=existing.id,
                event_type=AuditEventType.RECOVERY_VERIFIED,
                actor_type=ActorType.SYSTEM,
                metadata_={
                    "amount_recovered": payment.amount,
                    "reason": "payment_already_captured",
                },
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(audit)
            await self.db.flush()
        return existing

    async def get_case(self, case_id: uuid.UUID) -> Optional[RecoveryCase]:
        """Get a recovery case by ID."""
        result = await self.db.execute(
            select(RecoveryCase).where(RecoveryCase.id == case_id)
        )
        return result.scalar_one_or_none()

    async def list_cases(
        self,
        merchant_id: uuid.UUID,
        status: Optional[CaseStatus] = None,
        case_type: Optional[CaseType] = None,
        diagnosis_code: Optional[DiagnosisCode] = None,
        batch_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[RecoveryCase], int]:
        """List recovery cases with optional filters."""
        query = select(RecoveryCase).where(
            RecoveryCase.merchant_id == merchant_id
        )
        count_query = select(RecoveryCase).where(
            RecoveryCase.merchant_id == merchant_id
        )

        if status:
            query = query.where(RecoveryCase.status == status)
            count_query = count_query.where(RecoveryCase.status == status)
        if case_type:
            query = query.where(RecoveryCase.case_type == case_type)
            count_query = count_query.where(RecoveryCase.case_type == case_type)
        if diagnosis_code:
            query = query.where(RecoveryCase.diagnosis_code == diagnosis_code)
            count_query = count_query.where(
                RecoveryCase.diagnosis_code == diagnosis_code
            )
        if batch_id:
            query = query.where(RecoveryCase.batch_id == batch_id)
            count_query = count_query.where(RecoveryCase.batch_id == batch_id)

        # Get total count
        from sqlalchemy import func
        count_result = await self.db.execute(
            select(func.count()).select_from(count_query.subquery())
        )
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.order_by(RecoveryCase.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        cases = list(result.scalars().all())

        return cases, total
