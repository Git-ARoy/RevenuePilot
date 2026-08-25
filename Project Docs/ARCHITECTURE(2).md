# Architecture

## Architectural Objective

Build a small, modular agentic system that can reliably close a revenue-recovery loop while keeping financial state, policy enforcement, and external API execution deterministic.

The architecture intentionally separates:

1. **Data ingestion**
2. **Case detection**
3. **AI diagnosis/reasoning**
4. **Policy enforcement**
5. **Tool execution**
6. **Outcome verification**
7. **Metrics**
8. **Auditability**

The LLM is not the authority over money.

---

## Recommended Stack

### Frontend

**Next.js + TypeScript + Tailwind CSS**

Responsibilities:

- Merchant dashboard.
- Recovery case explorer.
- Agent activity timeline.
- Batch evaluation dashboard.
- Policy configuration.
- Simulation controls.
- Error/failure demonstration UI.

Do not put Razorpay secrets or business-critical recovery logic in the frontend.

### Backend

**Python + FastAPI**

Responsibilities:

- REST API.
- Razorpay integration.
- Webhook endpoint.
- Agent orchestration.
- Policy engine.
- Recovery state machine.
- Batch simulation.
- Metrics computation.
- Audit logging.

Python is preferred because the project benefits from rapid data processing, ML experimentation, and explicit typed service boundaries.

### Database

**PostgreSQL**

Use PostgreSQL for:

- Merchants.
- Customers.
- Orders.
- Payments.
- Recovery cases.
- Recovery attempts.
- Agent decisions.
- Policy configurations.
- Webhook events.
- Audit events.
- Batch runs.
- Evaluation results.

Do not introduce MongoDB unless a demonstrated requirement appears. Financial workflow state benefits from relational integrity and transactions.

### Cache / Background Work

**Redis** is optional.

Use it only for:

- Background job queues.
- Short-lived distributed locks.
- Rate limiting.
- Idempotency coordination.

For the first local MVP, FastAPI background tasks or a lightweight worker can be sufficient. Do not introduce Celery purely for architectural aesthetics.

### LLM

The LLM must be accessed through an internal abstraction:

```text
LLMProvider
  -> LocalProvider
  -> ExternalProvider
```

Preferred usage:

- Local model where feasible for cost and reproducibility.
- External model as an optional enhancement when available.

Recommended tasks:

- Ambiguous payment-failure explanation.
- Action rationale generation from structured evidence.
- Merchant-facing case summary.
- Optional message drafting.

The LLM must not decide whether a tool call is legally/safely allowed.

### ML / Scoring

Do not begin with a complex ML model.

MVP scoring can use a deterministic weighted recovery score based on:

- Failure reason.
- Number of prior attempts.
- Customer recency.
- Transaction amount.
- Payment method.
- Time since failure.
- Previous successful behavior.

A logistic regression or small tree-based model may later replace the heuristic if real/synthetic labeled data is adequate.

The scoring interface should therefore be abstracted:

```text
RecoveryScorer
  -> RuleBasedRecoveryScorer
  -> MLRecoveryScorer
```

This avoids coupling the orchestration layer to a specific model.

### Hosting

Local-first is the default.

Potential deployment target after MVP:

- Frontend: Vercel or equivalent.
- Backend: Render/Railway/Azure App Service or equivalent.
- PostgreSQL: managed PostgreSQL.
- Redis: managed Redis if required.

Deployment platform is not a core product decision. The repository must remain runnable locally with Docker Compose.

---

## External Integration

### Razorpay API

Most Razorpay APIs use:

```text
https://api.razorpay.com/v1
```

The application should use Razorpay Test Mode credentials.

The integration layer should support at minimum:

- Orders.
- Payments.
- Payment Links.
- Webhooks.

Relevant official documentation:

- https://razorpay.com/docs/api/
- https://razorpay.com/docs/api/orders/
- https://razorpay.com/docs/api/payments/
- https://razorpay.com/docs/api/payments/payment-links/
- https://razorpay.com/docs/webhooks/payments/

---

## System Diagram

```text
                       +----------------------+
                       |      Merchant UI     |
                       | Next.js / TypeScript |
                       +----------+-----------+
                                  |
                                  | REST / JSON
                                  v
                       +----------------------+
                       |     FastAPI API      |
                       +----------+-----------+
                                  |
              +-------------------+-------------------+
              |                   |                   |
              v                   v                   v
      +---------------+   +---------------+   +---------------+
      | Case Service  |   | Agent Service |   | Metrics       |
      | Detection     |   | Orchestration |   | & Evaluation  |
      +-------+-------+   +-------+-------+   +---------------+
              |                   |
              |                   +-------------------------+
              |                                             |
              v                                             v
      +---------------+                             +---------------+
      | Recovery Case |                             | Policy Engine |
      | State Machine |                             | Safety Gate   |
      +-------+-------+                             +-------+-------+
              |                                             |
              |                                             v
              |                                     +---------------+
              |                                     | Tool Gateway  |
              |                                     +-------+-------+
              |                                             |
              |                       +---------------------+------------------+
              |                       |                     |                  |
              |                       v                     v                  v
              |               Razorpay Payments     Payment Links       Internal Simulation
              |                       |                     |                  |
              +-----------------------+---------------------+------------------+
                                      |
                                      v
                              +---------------+
                              | Webhook/Event |
                              | Processor     |
                              +-------+-------+
                                      |
                                      v
                              +---------------+
                              | Reconciliation|
                              | + Verification|
                              +-------+-------+
                                      |
                                      v
                              +---------------+
                              | PostgreSQL    |
                              +---------------+
```

---

## Agent Execution Model

The agent should execute through a state machine, not an unrestricted planning loop.

### State Machine

```text
DETECTED
   |
   v
DIAGNOSED
   |
   v
ELIGIBILITY_CHECKED
   |
   +----> BLOCKED
   |
   v
STRATEGY_SELECTED
   |
   v
ACTION_PENDING
   |
   v
ACTION_EXECUTING
   |
   +----> ACTION_FAILED ----> RETRY_PENDING ----> ACTION_EXECUTING
   |                                      \
   |                                       -> ESCALATED
   |
   v
WAITING_FOR_OUTCOME
   |
   +----> RECOVERED
   |
   +----> UNRECOVERED
   |
   v
TERMINAL
```

The orchestrator must persist each transition.

---

## Data Flow

### 1. Ingestion

Razorpay event or simulator event enters the system.

```text
external event
  -> validate
  -> deduplicate
  -> persist raw event
  -> normalize
  -> update payment/order state
  -> detect recovery case
```

### 2. Case Detection

The Case Service checks whether the event creates or updates a recoverable revenue opportunity.

```text
payment failed
  -> identify amount
  -> identify customer
  -> identify reason
  -> check existing case
  -> create/update RecoveryCase
```

### 3. Diagnosis

The Agent Service prepares structured evidence.

The LLM may produce a diagnosis classification/explanation, but the evidence package must be deterministic.

Example:

```json
{
  "payment_status": "failed",
  "amount": 49900,
  "failure_code": "BAD_REQUEST_ERROR",
  "failure_description": "...",
  "attempt_count": 1,
  "elapsed_minutes": 22
}
```

The LLM output is converted into a constrained diagnosis schema.

### 4. Policy Decision

The Policy Engine decides whether the selected action is allowed.

```text
candidate action
  -> case state valid?
  -> amount within threshold?
  -> retry budget available?
  -> cooldown satisfied?
  -> action enabled?
  -> customer already contacted?
  -> no concurrent action?
  -> approve or block
```

### 5. Tool Execution

The Tool Gateway performs the actual API operation.

All calls go through adapters:

```text
Tool Gateway
  |
  +-- RazorpayAdapter
  |
  +-- SimulationAdapter
```

The orchestration layer should not know the HTTP details of Razorpay.

### 6. Verification

A successful tool response is only an action success.

Financial recovery requires an event/state verification.

```text
action succeeded
  -> wait for event
  -> fetch current payment/order state when needed
  -> reconcile
  -> classify recovered/unrecovered
  -> update metrics
```

---

## Data Model

### Merchant

```text
id
name
razorpay_key_id
mode
created_at
```

Never store `razorpay_key_secret` in plaintext.

For the buildathon, the secret should primarily live in environment variables/secrets management rather than the database.

### Customer

```text
id
external_customer_id
name
email
phone
metadata
created_at
```

### Order

```text
id
merchant_id
razorpay_order_id
amount
currency
status
created_at
updated_at
```

### Payment

```text
id
merchant_id
razorpay_payment_id
razorpay_order_id
customer_id
amount
currency
status
method
error_code
error_description
created_at
updated_at
```

### RecoveryCase

```text
id
merchant_id
payment_id
case_type
amount_at_risk
currency
status
diagnosis_code
diagnosis_confidence
recovery_score
current_strategy
attempt_count
max_attempts
next_eligible_at
terminal_reason
created_at
updated_at
```

### RecoveryAttempt

```text
id
recovery_case_id
attempt_number
action_type
status
idempotency_key
tool_request_hash
tool_response
error_code
started_at
completed_at
```

### AgentDecision

```text
id
recovery_case_id
stage
decision
reason_code
evidence
model_provider
model_name
confidence
created_at
```

Do not store hidden model chain-of-thought.

### WebhookEvent

```text
id
merchant_id
provider
provider_event_id
event_type
signature_valid
payload
received_at
processed_at
processing_status
```

### AuditEvent

```text
id
recovery_case_id
event_type
actor_type
actor_id
metadata
created_at
```

`actor_type` can be:

- `SYSTEM`
- `AGENT`
- `MERCHANT`
- `RAZORPAY_WEBHOOK`

### BatchRun

```text
id
mode
seed
started_at
completed_at
case_count
amount_at_risk
amount_recovered
recovery_rate
metrics
```

---

## Suggested Repository Structure

```text
revenuepilot/
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   │
│   └── api/
│       ├── app/
│       │   ├── main.py
│       │   ├── api/
│       │   ├── core/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── services/
│       │   ├── agents/
│       │   ├── policies/
│       │   ├── integrations/
│       │   │   └── razorpay/
│       │   ├── workers/
│       │   └── simulation/
│       └── tests/
│
├── packages/
│   └── shared-types/
│
├── scripts/
│   ├── seed.py
│   ├── simulate_batch.py
│   └── verify_metrics.py
│
├── docs/
│
├── docker-compose.yml
├── .env.example
├── README.md
├── PROJECT_OVERVIEW.md
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── API_SPEC.md
└── TECH_DECISIONS.md
```

---

## Key Design Decisions

### Financial state is deterministic

Payment/order states come from provider events or internal state transitions. An LLM must never invent a payment state.

### Policy is a separate layer

Agent reasoning can select a candidate action. The Policy Engine decides whether that action is actually permitted.

### Tools are adapters

Razorpay-specific HTTP details are isolated behind an adapter. This makes Simulation Mode and Test Mode interchangeable for the orchestration layer.

### Event-driven verification

The system treats recovery as a verified financial outcome rather than a successful API request.

### Structured AI output

LLM outputs must conform to schemas. Free-form text is not consumed by the policy engine.

### Reproducible evaluation

Simulation data must have deterministic random seeds.

### Audit-first design

Every significant state transition is persisted before the dashboard claims that something happened.
