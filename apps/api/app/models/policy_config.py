import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class PolicyConfig(Base):
    __tablename__ = "policy_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), unique=True, nullable=False)
    max_attempts = Column(Integer, default=3)
    retry_cooldown_seconds = Column(Integer, default=3600)
    max_automated_recovery_amount = Column(BigInteger, default=1000000)
    human_approval_threshold = Column(BigInteger, default=500000)
    allowed_actions = Column(JSON, nullable=False)
    escalation_threshold = Column(BigInteger, default=500000)
    model_selection = Column(String, default='default')
    simulation_mode = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
