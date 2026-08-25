import pytest
import uuid
from app.models.enums import CaseStatus, DiagnosisCode
from app.models.merchant import Merchant
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.services.diagnosis_service import DiagnosisService
from app.services.scoring_service import RuleBasedRecoveryScorer

@pytest.mark.asyncio
async def test_deterministic_diagnosis_from_error_code(db_session):
    merchant = Merchant(id=uuid.uuid4(), name="Merchant D", mode="test")
    db_session.add(merchant)
    await db_session.flush()

    payment = Payment(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        amount=49900,
        currency="INR",
        status="failed",
        error_code="GATEWAY_ERROR",
        error_description="The payment processing gateway returned an error"
    )
    db_session.add(payment)
    await db_session.flush()

    case = RecoveryCase(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        payment_id=payment.id,
        case_type="FAILED_PAYMENT",
        amount_at_risk=49900,
        currency="INR",
        status=CaseStatus.DETECTED
    )
    db_session.add(case)
    await db_session.flush()

    diagnosis_service = DiagnosisService(db_session)
    result = await diagnosis_service.diagnose(case, payment)

    assert result.code == DiagnosisCode.TRANSIENT_GATEWAY_FAILURE
    assert result.confidence >= 0.75
    assert case.diagnosis_code == DiagnosisCode.TRANSIENT_GATEWAY_FAILURE

@pytest.mark.asyncio
async def test_diagnosis_from_description_keywords(db_session):
    merchant = Merchant(id=uuid.uuid4(), name="Merchant E", mode="test")
    db_session.add(merchant)
    await db_session.flush()

    payment = Payment(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        amount=49900,
        currency="INR",
        status="failed",
        error_code="BAD_REQUEST_ERROR",
        error_description="Payment declined: insufficient balance in account."
    )
    db_session.add(payment)
    await db_session.flush()

    case = RecoveryCase(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        payment_id=payment.id,
        case_type="FAILED_PAYMENT",
        amount_at_risk=49900,
        currency="INR",
        status=CaseStatus.DETECTED
    )
    db_session.add(case)
    await db_session.flush()

    diagnosis_service = DiagnosisService(db_session)
    result = await diagnosis_service.diagnose(case, payment)

    assert result.code == DiagnosisCode.INSUFFICIENT_FUNDS
    assert result.confidence >= 0.85

def test_rule_based_scoring():
    scorer = RuleBasedRecoveryScorer()
    
    case = RecoveryCase(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        payment_id=uuid.uuid4(),
        case_type="FAILED_PAYMENT",
        amount_at_risk=49900,
        status=CaseStatus.DIAGNOSED,
        diagnosis_code=DiagnosisCode.TRANSIENT_GATEWAY_FAILURE,
        attempt_count=0
    )
    payment = Payment(
        id=case.payment_id,
        merchant_id=case.merchant_id,
        amount=49900,
        method="card",
        status="failed"
    )

    score, factors = scorer.score(case, payment)
    assert 0.70 <= score <= 1.0
    assert factors.attempt_penalty == 1.0
    assert factors.failure_reason_score == 0.85
