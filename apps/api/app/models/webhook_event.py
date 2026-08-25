import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.enums import WebhookProcessingStatus

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), nullable=True)
    provider = Column(String, default='razorpay')
    provider_event_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    signature_valid = Column(Boolean, nullable=False)
    payload = Column(JSON, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_status = Column(SQLEnum(WebhookProcessingStatus), nullable=False)
