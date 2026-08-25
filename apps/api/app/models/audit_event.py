import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import AuditEventType, ActorType

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recovery_case_id = Column(UUID(as_uuid=True), ForeignKey('recovery_cases.id'), nullable=True)
    event_type = Column(SQLEnum(AuditEventType), nullable=False)
    actor_type = Column(SQLEnum(ActorType), nullable=False)
    actor_id = Column(String, nullable=True)
    metadata_ = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
