import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON, Enum as SQLEnum, Float, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import BatchStatus

class BatchRun(Base):
    __tablename__ = "batch_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), nullable=False)
    mode = Column(String, nullable=False)
    seed = Column(Integer, nullable=True)
    config = Column(JSON, nullable=True)
    status = Column(SQLEnum(BatchStatus), default=BatchStatus.PENDING)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    case_count = Column(Integer, default=0)
    amount_at_risk = Column(BigInteger, default=0)
    amount_recovered = Column(BigInteger, default=0)
    recovery_rate = Column(Float, default=0.0)
    metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
