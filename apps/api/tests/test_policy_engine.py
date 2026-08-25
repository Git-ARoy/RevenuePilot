import pytest
import uuid
from app.models.enums import CaseStatus, ActionType
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.policy_config import PolicyConfig
from app.policies.policy_engine import PolicyEngine

@pytest.mark.asyncio
async def test_policy_engine_max_attempts(db_session):
    merchant = Merchant(id=uuid.uuid4(), name="Merchant A", mode="test")
    db_session.add(merchant)
    
    payment = Payment(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        amount=49900,
        currency="INR",
        status="failed"
    )
    db_session.add(payment)
    await db_session.flush()

    policy = PolicyConfig(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        max_attempts=2,
        max_automated_recovery_amount=1000000,
        human_approval_threshold=500000,
        allowed_actions=[ActionType.CREATE_PAYMENT_LINK.value, ActionType.RETRY_PAYMENT.value]
    )
    db_session.add(policy)
    await db_session.flush()

    case = RecoveryCase(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        payment_id=payment.id,
        case_type="FAILED_PAYMENT",
        amount_at_risk=49900,
        currency="INR",
        status=CaseStatus.STRATEGY_SELECTED,
        attempt_count=2,  # Reached max attempts
        max_attempts=2
    )
    db_session.add(case)
    await db_session.flush()

    engine = PolicyEngine(db_session)
    decision = await engine.evaluate(case, ActionType.CREATE_PAYMENT_LINK)

    assert decision.allowed is False
    assert "Attempt count 2 / 2" in decision.block_reason

@pytest.mark.asyncio
async def test_policy_engine_amount_limit(db_session):
    merchant = Merchant(id=uuid.uuid4(), name="Merchant B", mode="test")
    db_session.add(merchant)
    
    payment = Payment(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        amount=200000,
        currency="INR",
        status="failed"
    )
    db_session.add(payment)
    await db_session.flush()

    policy = PolicyConfig(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        max_attempts=3,
        max_automated_recovery_amount=100000,  # ₹1,000 max
        human_approval_threshold=50000,
        allowed_actions=[ActionType.CREATE_PAYMENT_LINK.value]
    )
    db_session.add(policy)
    await db_session.flush()

    case = RecoveryCase(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        payment_id=payment.id,
        case_type="FAILED_PAYMENT",
        amount_at_risk=200000,  # ₹2,000 exceeds limit
        currency="INR",
        status=CaseStatus.STRATEGY_SELECTED,
        attempt_count=0
    )
    db_session.add(case)
    await db_session.flush()

    engine = PolicyEngine(db_session)
    decision = await engine.evaluate(case, ActionType.CREATE_PAYMENT_LINK)

    assert decision.allowed is False
    assert "AMOUNT_LIMIT" in decision.block_reason

@pytest.mark.asyncio
async def test_policy_engine_allowed_action(db_session):
    merchant = Merchant(id=uuid.uuid4(), name="Merchant C", mode="test")
    db_session.add(merchant)
    
    payment = Payment(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        amount=49900,
        currency="INR",
        status="failed"
    )
    db_session.add(payment)
    await db_session.flush()

    policy = PolicyConfig(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        max_attempts=3,
        max_automated_recovery_amount=1000000,
        human_approval_threshold=500000,
        allowed_actions=[ActionType.CREATE_PAYMENT_LINK.value]
    )
    db_session.add(policy)
    await db_session.flush()

    case = RecoveryCase(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        payment_id=payment.id,
        case_type="FAILED_PAYMENT",
        amount_at_risk=49900,
        currency="INR",
        status=CaseStatus.STRATEGY_SELECTED,
        attempt_count=0
    )
    db_session.add(case)
    await db_session.flush()

    engine = PolicyEngine(db_session)
    decision = await engine.evaluate(case, ActionType.RETRY_PAYMENT)

    assert decision.allowed is False
    assert "ACTION_ALLOWED" in decision.block_reason
