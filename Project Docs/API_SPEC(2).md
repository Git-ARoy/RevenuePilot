# API Specification

## Scope

This document defines the **internal RevenuePilot API** and the required upstream Razorpay integration points.

The internal API is owned by FastAPI.

The frontend must never call Razorpay directly with secret credentials.

---

# 1. Authentication

## Internal API

For the buildathon MVP, use one of:

- Development mode: a signed local/session token.
- Production-like deployment: JWT or secure session cookie.

The exact auth implementation can remain lightweight because the project is a single-merchant demo.

Every protected endpoint must derive `merchant_id` from authenticated server-side context rather than accepting an arbitrary merchant identifier from the browser.

## Razorpay Authentication

Razorpay API credentials must remain server-side.

Use Razorpay's documented API authentication mechanism.

Do not expose:

```text
RAZORPAY_KEY_SECRET
```

to the frontend.

Use environment variables:

```text
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
RAZORPAY_MODE=test
```

---

# 2. API Conventions

Base URL:

```text
/api
```

Responses:

```json
{
  "data": {},
  "error": null,
  "request_id": "req_..."
}
```

Errors:

```json
{
  "data": null,
  "error": {
    "code": "RECOVERY_POLICY_BLOCKED",
    "message": "Maximum retry attempts reached"
  },
  "request_id": "req_..."
}
```

Use HTTP status codes consistently:

- `200` successful read/update.
- `201` resource created.
- `202` action accepted for asynchronous execution.
- `400` malformed request.
- `401` unauthenticated.
- `403` authenticated but not permitted.
- `404` resource not found.
- `409` idempotency/conflict.
- `422` schema validation.
- `429` rate limited.
- `500` unexpected server failure.
- `502/503` upstream integration failure.

---

# 3. Dashboard

## GET `/api/dashboard/summary`

Returns merchant-level recovery metrics.

### Response

```json
{
  "data": {
    "amount_at_risk": 1042500,
    "amount_recovered": 387200,
    "recovery_rate": 37.15,
    "active_cases": 84,
    "escalated_cases": 11,
    "failed_actions": 4,
    "period": {
      "from": "2026-08-24T00:00:00Z",
      "to": "2026-08-24T23:59:59Z"
    }
  },
  "error": null,
  "request_id": "..."
}
```

Amounts are stored and returned in currency subunits.

---

# 4. Recovery Cases

## GET `/api/recovery-cases`

Query parameters:

```text
status
case_type
diagnosis_code
page
page_size
```

### Response

```json
{
  "data": {
    "items": [
      {
        "id": "case_123",
        "case_type": "FAILED_PAYMENT",
        "amount_at_risk": 49900,
        "currency": "INR",
        "status": "ACTION_PENDING",
        "diagnosis_code": "TRANSIENT_GATEWAY_FAILURE",
        "recovery_score": 0.81,
        "attempt_count": 0,
        "current_strategy": "CREATE_PAYMENT_LINK",
        "created_at": "2026-08-24T10:30:00Z"
      }
    ],
    "page": 1,
    "page_size": 25,
    "total": 84
  },
  "error": null,
  "request_id": "..."
}
```

## GET `/api/recovery-cases/{case_id}`

Returns full case state.

### Response

```json
{
  "data": {
    "id": "case_123",
    "status": "RECOVERED",
    "amount_at_risk": 49900,
    "amount_recovered": 49900,
    "currency": "INR",
    "diagnosis": {
      "code": "TRANSIENT_GATEWAY_FAILURE",
      "confidence": 0.94,
      "reason": "Failure appears transient and case remains within retry policy."
    },
    "strategy": "CREATE_PAYMENT_LINK",
    "attempt_count": 1,
    "timeline": [
      {
        "event": "CASE_DETECTED",
        "timestamp": "..."
      },
      {
        "event": "CASE_DIAGNOSED",
        "timestamp": "..."
      },
      {
        "event": "ACTION_EXECUTED",
        "timestamp": "..."
      },
      {
        "event": "RECOVERY_VERIFIED",
        "timestamp": "..."
      }
    ]
  },
  "error": null,
  "request_id": "..."
}
```

---

# 5. Trigger Recovery Evaluation

## POST `/api/recovery-cases/{case_id}/evaluate`

Evaluates a case without executing an action.

This endpoint is useful for debugging and for showing the agent's proposed decision before the policy gate.

### Response

```json
{
  "data": {
    "case_id": "case_123",
    "diagnosis": {
      "code": "TRANSIENT_GATEWAY_FAILURE",
      "confidence": 0.94
    },
    "candidate_action": {
      "type": "CREATE_PAYMENT_LINK",
      "reason_code": "PAYMENT_METHOD_REENTRY"
    },
    "policy": {
      "allowed": true,
      "checks": [
        {
          "rule": "MAX_ATTEMPTS",
          "passed": true
        },
        {
          "rule": "AMOUNT_LIMIT",
          "passed": true
        }
      ]
    }
  },
  "error": null,
  "request_id": "..."
}
```

This endpoint must not execute financial actions.

---

# 6. Execute Recovery Action

## POST `/api/recovery-cases/{case_id}/actions`

### Request

```json
{
  "action_type": "CREATE_PAYMENT_LINK",
  "reason_code": "PAYMENT_METHOD_REENTRY"
}
```

### Required Headers

```text
Idempotency-Key: <unique-per-intended-action>
```

### Response

```json
{
  "data": {
    "attempt_id": "attempt_123",
    "status": "EXECUTED",
    "action_type": "CREATE_PAYMENT_LINK",
    "external_reference": "plink_123",
    "next_state": "WAITING_FOR_OUTCOME"
  },
  "error": null,
  "request_id": "..."
}
```

If the same idempotency key is submitted again, the API must return the original result rather than creating a duplicate recovery action.

---

# 7. Escalation

## POST `/api/recovery-cases/{case_id}/escalate`

### Request

```json
{
  "reason_code": "MAX_RETRY_BUDGET_EXHAUSTED",
  "notes": "No successful recovery after two permitted actions."
}
```

### Response

```json
{
  "data": {
    "case_id": "case_123",
    "status": "ESCALATED"
  },
  "error": null,
  "request_id": "..."
}
```

---

# 8. Policy Configuration

## GET `/api/policies`

Returns current merchant recovery policy.

## PUT `/api/policies`

### Request

```json
{
  "max_attempts": 2,
  "retry_cooldown_seconds": 3600,
  "max_automated_recovery_amount": 1000000,
  "human_approval_threshold": 500000,
  "allowed_actions": [
    "CREATE_PAYMENT_LINK",
    "SCHEDULE_RETRY"
  ]
}
```

### Constraints

- `max_attempts` must be finite.
- Amount thresholds must be non-negative.
- A merchant cannot configure an action that the backend does not support.
- Policy updates must produce an audit event.

---

# 9. Simulation

## POST `/api/simulation/generate`

### Request

```json
{
  "seed": 42,
  "count": 100,
  "amount_min": 10000,
  "amount_max": 500000,
  "scenario_mix": {
    "transient_failure": 0.25,
    "insufficient_funds": 0.20,
    "payment_method_failure": 0.15,
    "bank_decline": 0.10,
    "checkout_abandonment": 0.10,
    "already_recovered": 0.10,
    "non_recoverable": 0.05,
    "ambiguous": 0.05
  }
}
```

### Response

```json
{
  "data": {
    "batch_id": "batch_123",
    "case_count": 100
  },
  "error": null,
  "request_id": "..."
}
```

---

# 10. Simulation Run

## POST `/api/simulation/batches/{batch_id}/run`

### Request

```json
{
  "mode": "FULL_AGENT"
}
```

### Response

```json
{
  "data": {
    "batch_id": "batch_123",
    "status": "COMPLETED",
    "metrics": {
      "cases": 100,
      "amount_at_risk": 2750000,
      "amount_recovered": 1015000,
      "recovery_rate": 36.91,
      "actions_attempted": 73,
      "escalations": 9,
      "terminal_failures": 4
    }
  },
  "error": null,
  "request_id": "..."
}
```

The example values are illustrative only. Tests must calculate actual metrics.

---

# 11. Batch Results

## GET `/api/simulation/batches/{batch_id}`

Returns:

- Seed.
- Scenario distribution.
- Case count.
- Amount at risk.
- Amount recovered.
- Recovery rate.
- Action distribution.
- Failure distribution.
- Escalation distribution.
- Per-case results.

---

# 12. Audit Timeline

## GET `/api/recovery-cases/{case_id}/audit`

### Response

```json
{
  "data": {
    "events": [
      {
        "event_type": "CASE_DETECTED",
        "actor_type": "SYSTEM",
        "metadata": {
          "amount_at_risk": 49900
        },
        "created_at": "..."
      },
      {
        "event_type": "ACTION_PROPOSED",
        "actor_type": "AGENT",
        "metadata": {
          "action": "CREATE_PAYMENT_LINK",
          "reason_code": "PAYMENT_METHOD_REENTRY"
        },
        "created_at": "..."
      }
    ]
  },
  "error": null,
  "request_id": "..."
}
```

---

# 13. Razorpay Webhook

## POST `/api/webhooks/razorpay`

This endpoint is unauthenticated at the application-auth layer but authenticated using Razorpay's webhook signature.

Required behavior:

1. Read raw request body.
2. Validate the Razorpay signature using the configured webhook secret.
3. Reject invalid signatures.
4. Persist the raw event.
5. Deduplicate using provider event identity.
6. Process the event idempotently.
7. Return a success response only after durable persistence.

Razorpay documents that the signature is passed in the `X-Razorpay-Signature` header.

Do not parse and reserialize the request body before signature verification.

---

# 14. Razorpay Upstream API Integration

The backend should encapsulate provider calls behind:

```python
class RazorpayClient:
    async def create_order(...)
    async def get_order(...)
    async def get_order_payments(...)
    async def get_payment(...)
    async def create_payment_link(...)
    async def resend_payment_link(...)
```

Additional methods may be added only when required by the selected recovery workflow.

Razorpay's API reference currently documents:

- `POST /v1/orders`
- `GET /v1/orders/:id`
- `GET /v1/orders/:id/payments`
- `GET /v1/payments/:id`
- Payment Link APIs under `/v1/payment_links`
- Payment capture under `/v1/payments/:id/capture`

Do not use payment capture as a generic recovery mechanism. Capture is for moving an authorized payment to captured status, not for initiating a new customer payment.

---

# 15. Provider-to-Internal State Mapping

Example internal states:

```text
RECOVERY_CASE:
  DETECTED
  DIAGNOSED
  ACTION_PENDING
  ACTION_EXECUTING
  WAITING_FOR_OUTCOME
  RECOVERED
  ESCALATED
  STOPPED
  FAILED
```

Provider states must be mapped explicitly.

Do not let provider status strings directly become internal agent states.

---

# 16. API Security Rules

- Never return Razorpay secrets.
- Never allow arbitrary Razorpay endpoint paths from clients.
- Never allow arbitrary tool names from LLM output.
- Validate all request bodies.
- Rate-limit action execution endpoints.
- Require idempotency for consequential actions.
- Log policy blocks.
- Do not expose internal prompt text.
- Do not expose hidden chain-of-thought.
- Use structured error codes.

---

# 17. API Design Principle

The internal API should make unsafe behavior difficult by construction.

A client can request:

```text
"execute CREATE_PAYMENT_LINK for case_123"
```

but the backend still independently checks:

```text
case exists
AND case is eligible
AND action is permitted
AND retry budget remains
AND amount threshold passes
AND cooldown passes
AND no concurrent attempt exists
AND idempotency key is unique
```

Only after all gates pass should the Razorpay adapter be called.
