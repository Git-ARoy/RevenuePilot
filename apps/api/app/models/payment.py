import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), nullable=False)
    razorpay_payment_id = Column(String, unique=True, nullable=True)
    razorpay_order_id = Column(String, nullable=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=True)
    amount = Column(BigInteger, nullable=False)
    currency = Column(String(3), default='INR')
    status = Column(String, nullable=False)
    method = Column(String, nullable=True)
    error_code = Column(String, nullable=True)
    error_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
