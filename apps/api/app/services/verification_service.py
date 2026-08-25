import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import CaseStatus, AuditEventType, ActorType
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.recovery_attempt import RecoveryAttempt
from app.models.audit_event import AuditEvent

class VerificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_payment(self, payment_id: uuid.UUID) -> Optional[RecoveryCase]:
        payment = (await self.db.execute(select(Payment).where(Payment.id == payment_id))).scalar_one_or_none()
        if not payment or payment.status != "captured":
            return None

        case = (await self.db.execute(select(RecoveryCase).where(RecoveryCase.payment_id == payment.id))).scalar_one_or_none()
        if case and case.status not in [CaseStatus.RECOVERED, CaseStatus.TERMINAL]:
            case.status = CaseStatus.RECOVERED
            case.amount_recovered = payment.amount
            
            audit = AuditEvent(
                recovery_case_id=case.id,
                event_type=AuditEventType.RECOVERY_VERIFIED,
                actor_type=ActorType.SYSTEM,
                metadata_={"payment_id": str(payment.id), "amount": payment.amount}
            )
            self.db.add(audit)
            await self.db.flush()
            return case
        return None

    async def check_payment_link_outcome(self, payment_link_id: str) -> Optional[RecoveryCase]:
        attempt = (await self.db.execute(
            select(RecoveryAttempt).where(RecoveryAttempt.external_reference == payment_link_id)
        )).scalar_one_or_none()
        
        if not attempt:
            return None
            
        case = (await self.db.execute(select(RecoveryCase).where(RecoveryCase.id == attempt.recovery_case_id))).scalar_one_or_none()
        if not case:
            return None
            
        # Simplified placeholder for checking if linked payments exist and are captured
        return None
