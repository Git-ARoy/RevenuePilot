import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger, Enum as SQLEnum, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import CaseType, CaseStatus, DiagnosisCode, ActionType

class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), nullable=False)
    payment_id = Column(UUID(as_uuid=True), ForeignKey('payments.id'), nullable=False)
    batch_id = Column(UUID(as_uuid=True), nullable=True) # Assuming batch_runs table might be created later or ForeignKey omitted if ok
    case_type = Column(SQLEnum(CaseType), nullable=False)
    amount_at_risk = Column(BigInteger, nullable=False)
    amount_recovered = Column(BigInteger, default=0)
    currency = Column(String(3), default='INR')
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.DETECTED)
    diagnosis_code = Column(SQLEnum(DiagnosisCode), nullable=True)
    diagnosis_confidence = Column(Float, nullable=True)
    recovery_score = Column(Float, nullable=True)
    current_strategy = Column(SQLEnum(ActionType), nullable=True)
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_eligible_at = Column(DateTime(timezone=True), nullable=True)
    terminal_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
