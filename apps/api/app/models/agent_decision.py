import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recovery_case_id = Column(UUID(as_uuid=True), ForeignKey('recovery_cases.id'), nullable=False)
    stage = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    reason_code = Column(String, nullable=True)
    evidence = Column(JSON, nullable=True)
    model_provider = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
