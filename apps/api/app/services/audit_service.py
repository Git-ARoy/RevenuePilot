import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_event import AuditEvent
from app.models.enums import AuditEventType, ActorType

class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def log_event(self, case_id: uuid.UUID, event_type: AuditEventType, actor_type: ActorType, metadata: dict, actor_id: Optional[str] = None):
        audit = AuditEvent(
            recovery_case_id=case_id,
            event_type=event_type,
            actor_type=actor_type,
            metadata_=metadata,
            actor_id=actor_id
        )
        self.db.add(audit)
        await self.db.flush()
        return audit
        
    async def get_timeline(self, case_id: uuid.UUID) -> List[AuditEvent]:
        stmt = select(AuditEvent).where(AuditEvent.recovery_case_id == case_id).order_by(AuditEvent.created_at.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
