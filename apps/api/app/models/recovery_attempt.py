import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum as SQLEnum, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.enums import ActionType, AttemptStatus

class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recovery_case_id = Column(UUID(as_uuid=True), ForeignKey('recovery_cases.id'), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    action_type = Column(SQLEnum(ActionType), nullable=False)
    status = Column(SQLEnum(AttemptStatus), nullable=False)
    idempotency_key = Column(String, unique=True, nullable=False)
    tool_request_hash = Column(String, nullable=True)
    tool_response = Column(JSON, nullable=True)
    external_reference = Column(String, nullable=True)
    error_code = Column(String, nullable=True)
    error_description = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
