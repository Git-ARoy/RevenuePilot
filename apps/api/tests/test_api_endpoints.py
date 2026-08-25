import pytest
import pytest_asyncio
import uuid
import json
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_health_and_dashboard_summary(api_client):
    # Health check
    resp = await api_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    # Dashboard summary
    resp = await api_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert "amount_at_risk" in body["data"]
    assert "recovery_rate" in body["data"]

@pytest.mark.asyncio
async def test_simulation_workflow_api(api_client):
    # 1. Generate batch
    gen_resp = await api_client.post(
        "/api/simulation/generate",
        json={"seed": 100, "count": 20, "amount_min": 10000, "amount_max": 200000}
    )
    assert gen_resp.status_code == 200
    gen_body = gen_resp.json()
    batch_id = gen_body["data"]["batch_id"]
    assert batch_id is not None
    assert gen_body["data"]["case_count"] == 20

    # 2. Run batch
    run_resp = await api_client.post(
        f"/api/simulation/batches/{batch_id}/run",
        json={"mode": "FULL_AGENT"}
    )
    assert run_resp.status_code == 200
    run_body = run_resp.json()
    assert run_body["data"]["status"] == "COMPLETED"
    assert "metrics" in run_body["data"]
    metrics = run_body["data"]["metrics"]
    assert metrics["cases"] == 20
    assert metrics["amount_at_risk"] > 0
    assert metrics["amount_recovered"] >= 0

    # 3. Get batch detail
    batch_detail_resp = await api_client.get(f"/api/simulation/batches/{batch_id}")
    assert batch_detail_resp.status_code == 200
    detail_body = batch_detail_resp.json()
    assert detail_body["data"]["id"] == batch_id

    # 4. List batches
    batches_list_resp = await api_client.get("/api/simulation/batches")
    assert batches_list_resp.status_code == 200
    assert len(batches_list_resp.json()["data"]) >= 1

@pytest.mark.asyncio
async def test_recovery_case_lifecycle_api(api_client):
    # First generate a batch with 5 cases
    gen_resp = await api_client.post(
        "/api/simulation/generate",
        json={"seed": 200, "count": 5, "amount_min": 20000, "amount_max": 100000}
    )
    batch_id = gen_resp.json()["data"]["batch_id"]

    # List cases
    cases_resp = await api_client.get(f"/api/recovery-cases?batch_id={batch_id}")
    assert cases_resp.status_code == 200
    cases_data = cases_resp.json()["data"]["items"]
    assert len(cases_data) == 5
    case_id = cases_data[0]["id"]

    # Get case detail with timeline
    case_detail_resp = await api_client.get(f"/api/recovery-cases/{case_id}")
    assert case_detail_resp.status_code == 200
    detail_body = case_detail_resp.json()["data"]
    assert detail_body["case"]["id"] == case_id
    assert "timeline" in detail_body

    # Evaluate case (dry-run)
    eval_resp = await api_client.post(f"/api/recovery-cases/{case_id}/evaluate")
    assert eval_resp.status_code == 200
    eval_body = eval_resp.json()["data"]
    assert "diagnosis" in eval_body
    assert "candidate_action" in eval_body
    assert "policy" in eval_body

    # Execute action with Idempotency-Key
    idem_key = f"test_idem_{uuid.uuid4().hex}"
    act_resp = await api_client.post(
        f"/api/recovery-cases/{case_id}/actions",
        json={"action_type": "CREATE_PAYMENT_LINK", "reason_code": "TEST_ACTION"},
        headers={"Idempotency-Key": idem_key}
    )
    assert act_resp.status_code == 200
    act_body = act_resp.json()["data"]
    assert act_body["id"] == case_id

    # Escalate case
    esc_resp = await api_client.post(
        f"/api/recovery-cases/{case_id}/escalate",
        json={"reason_code": "MANUAL_REVIEW_NEEDED", "notes": "Risk team flagged customer"}
    )
    assert esc_resp.status_code == 200
    esc_body = esc_resp.json()["data"]
    assert esc_body["status"] == "ESCALATED"

    # Get audit timeline
    audit_resp = await api_client.get(f"/api/recovery-cases/{case_id}/audit")
    assert audit_resp.status_code == 200
    events = audit_resp.json()["data"]["events"]
    assert len(events) >= 2

@pytest.mark.asyncio
async def test_policy_config_api(api_client):
    # Get current policy
    get_resp = await api_client.get("/api/policies")
    assert get_resp.status_code == 200
    policy_data = get_resp.json()["data"]
    assert "max_attempts" in policy_data

    # Update policy
    put_resp = await api_client.put(
        "/api/policies",
        json={
            "max_attempts": 4,
            "retry_cooldown_seconds": 1800,
            "max_automated_recovery_amount": 2000000,
            "human_approval_threshold": 750000,
            "allowed_actions": ["CREATE_PAYMENT_LINK", "RETRY_PAYMENT", "SCHEDULE_RETRY"]
        }
    )
    assert put_resp.status_code == 200
    updated_data = put_resp.json()["data"]
    assert updated_data["max_attempts"] == 4
    assert updated_data["retry_cooldown_seconds"] == 1800
    assert updated_data["human_approval_threshold"] == 750000

@pytest.mark.asyncio
async def test_razorpay_webhook_api(api_client):
    # Construct simulated Razorpay payment.captured webhook payload
    payload = {
        "entity": "event",
        "account_id": "acc_sim_123",
        "event": "payment.captured",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_{uuid.uuid4().hex[:12]}",
                    "amount": 49900,
                    "currency": "INR",
                    "status": "captured",
                    "method": "upi"
                }
            }
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")

    # Send webhook
    resp = await api_client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": "dev_test_sig"}
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["event_type"] == "payment.captured"
    assert body["status"] in ["PROCESSED", "PENDING"]
