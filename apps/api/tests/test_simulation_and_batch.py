import pytest
import uuid
from app.models.enums import BatchStatus, CaseStatus
from app.models.merchant import Merchant
from app.models.policy_config import PolicyConfig
from app.models.enums import ActionType
from app.simulation.generator import ScenarioGenerator
from app.simulation.batch_runner import BatchRunner

@pytest.mark.asyncio
async def test_full_simulation_batch_pipeline(db_session):
    # 1. Create merchant and policy
    merchant = Merchant(id=uuid.uuid4(), name="Test Merchant", mode="test")
    db_session.add(merchant)
    
    policy = PolicyConfig(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        max_attempts=3,
        retry_cooldown_seconds=3600,
        max_automated_recovery_amount=1000000,
        human_approval_threshold=500000,
        allowed_actions=[
            ActionType.RETRY_PAYMENT.value,
            ActionType.CREATE_PAYMENT_LINK.value,
            ActionType.RESEND_PAYMENT_LINK.value,
            ActionType.SCHEDULE_RETRY.value,
            ActionType.SEND_RECOVERY_PROMPT.value,
            ActionType.ESCALATE_TO_HUMAN.value,
            ActionType.STOP_RECOVERY.value
        ]
    )
    db_session.add(policy)
    await db_session.commit()

    # 2. Generate batch of 100 synthetic cases with seed 42
    generator = ScenarioGenerator(db_session, seed=42)
    batch = await generator.generate_batch(
        merchant_id=merchant.id,
        count=100,
        amount_min=10000,
        amount_max=300000
    )
    await db_session.commit()

    assert batch.case_count == 100
    assert batch.amount_at_risk > 0
    assert batch.status == BatchStatus.PENDING

    # 3. Run full agent batch evaluation
    runner = BatchRunner(db_session, seed=42)
    metrics = await runner.run_batch(batch.id)

    # 4. Verify measurable metrics derived from actual case outcomes
    assert metrics["cases"] == 100
    assert metrics["amount_at_risk"] == batch.amount_at_risk
    assert metrics["amount_recovered"] > 0
    assert 0 < metrics["recovery_rate"] <= 100.0
    assert metrics["actions_attempted"] > 0
    assert metrics["recovered_cases"] > 0
    assert metrics["escalations"] >= 0

    print("\n--- BATCH METRICS RESULT ---")
    print(f"Total Cases: {metrics['cases']}")
    print(f"Amount at Risk: ₹{metrics['amount_at_risk'] / 100:,.2f}")
    print(f"Amount Recovered: ₹{metrics['amount_recovered'] / 100:,.2f}")
    print(f"Recovery Rate: {metrics['recovery_rate']}%")
    print(f"Actions Executed: {metrics['actions_attempted']}")
    print(f"Successful Recoveries: {metrics['recovered_cases']}")
    print(f"Escalations: {metrics['escalations']}")
