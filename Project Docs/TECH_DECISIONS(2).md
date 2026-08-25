# Technical Decisions

## Purpose

This document records decisions that constrain the architecture so future coding agents do not repeatedly propose alternatives that have already been evaluated and rejected.

The project is intentionally optimized for:

- Solo development.
- High implementation velocity.
- Strong engineering credibility.
- Measurable revenue recovery.
- Safe agent behavior.
- Low infrastructure cost.
- Reproducible evaluation.

---

# 1. Track Selection

## Decision

Build for **Track 3: AI Revenue Recovery**.

## Why

This track maps directly to the strongest project thesis for the buildathon:

```text
detect revenue at risk
-> diagnose
-> decide
-> act
-> verify
-> recover
```

It provides a measurable business KPI: recovered money.

It also provides a natural place to demonstrate agentic behavior, API integration, state management, failure recovery, and safety controls.

## Rejected Alternatives

### Track 1: AI Growth & Agentic Commerce

Not rejected as a bad track. Rejected for this submission because it has a wider integration surface and a harder-to-fake requirement: the system needs to convincingly demonstrate AI-buyer/merchant transactionability or meaningful revenue growth.

### Track 2: AI Risk Manager

Technically strong but less aligned with the desired demonstration of autonomous workflow execution and business-value closure. Evaluation also heavily depends on credible precision/recall and held-out data.

### Track 4: AI Finance Controller

Good engineering problem but less directly aligned with the agentic recovery thesis. The primary KPI is reconciliation/matching accuracy rather than recovered revenue.

### Track 5: Open Track

Freedom is not itself an advantage. An open project could create a weaker problem statement and dilute the Razorpay-specific value proposition.

---

# 2. Production-Style Agent Instead of Chatbot

## Decision

Do not build a conversational chatbot as the core product.

The primary interface is an operations dashboard.

A conversational layer may be added later for merchant Q&A, but it is not the product's main workflow.

## Why

The track asks for an agent that executes a bounded recovery workflow. A chatbot can explain a problem without solving it.

The product must demonstrate:

```text
action + outcome
```

not:

```text
answer + prose
```

---

# 3. Deterministic Policy Engine + AI Reasoning

## Decision

Use a hybrid architecture:

```text
LLM / scoring
       |
       v
candidate decision
       |
       v
deterministic policy gate
       |
       v
tool execution
```

## Why

Financial actions cannot depend entirely on probabilistic model output.

The policy engine is responsible for:

- Retry limits.
- Amount limits.
- Cooldowns.
- Supported action types.
- Terminal states.
- Escalation.
- Idempotency.
- Concurrency protection.

This also directly demonstrates AI judgment: AI is used where ambiguity benefits from reasoning; deterministic code handles invariants.

## Rejected

### LLM controls tools directly

Rejected.

The LLM should never have unrestricted access to arbitrary HTTP tools or provider endpoints.

---

# 4. Do Not Use an LLM for Payment State

## Decision

Payment status and financial state are deterministic data.

## Why

An LLM cannot be the source of truth for:

- Captured amount.
- Payment status.
- Order state.
- Retry count.
- Recovery amount.
- Whether a webhook arrived.

These values must originate from provider data or internal transactional state.

---

# 5. LLM Usage

## Decision

Use an LLM selectively for:

- Ambiguous failure diagnosis.
- Structured recovery reasoning from provided evidence.
- Human-readable explanations.
- Optional message drafting.

Require structured JSON output.

## Rejected

### Send every transaction to an LLM

Rejected because it:

- Increases cost.
- Adds latency.
- Reduces reproducibility.
- Creates unnecessary failure points.
- Demonstrates poor AI judgment.

---

# 6. Local-First AI With Provider Abstraction

## Decision

The application must not hard-code one model provider into business logic.

Use:

```text
LLMProvider
  -> LocalProvider
  -> ExternalProvider
```

The implementation may start with one provider, but all application code should use the interface.

## Why

This keeps the buildathon project inexpensive and allows local inference during development/evaluation.

Potential local inference can be used with a small quantized model through an adapter such as Ollama or another local runtime.

An external provider may be enabled when stronger reasoning is useful.

## Rejected

### Hard-wire Gemini/OpenAI/another vendor into the agent

Rejected because it couples the core orchestration logic to billing, availability, and vendor APIs.

---

# 7. PostgreSQL Over MongoDB

## Decision

Use PostgreSQL as the source of truth.

## Why

The domain has relational financial entities:

```text
merchant
customer
order
payment
recovery_case
recovery_attempt
agent_decision
webhook_event
audit_event
batch_run
```

Transactions, foreign keys, uniqueness constraints, and idempotency records are important.

## Rejected

### MongoDB as primary database

Rejected for the MVP because the core problem is transactional workflow state, not unstructured document storage.

---

# 8. Next.js + FastAPI

## Decision

Use:

- Next.js / TypeScript / Tailwind for frontend.
- FastAPI / Python for backend.

## Why

This matches the existing project skillset and allows:

- Fast UI development.
- Strong type contracts on frontend.
- Rapid API implementation.
- Python-native data/ML tooling.
- Clean separation between UI and financial logic.

## Rejected

### Full-stack Next.js only

Rejected because the agent, data processing, ML experimentation, provider integrations, and batch simulation are more naturally isolated in Python.

### Python-only UI

Rejected because the build requires a polished operations dashboard and fast frontend iteration.

---

# 9. Razorpay Integration Through an Adapter

## Decision

Use:

```text
RazorpayClient / RazorpayAdapter
```

instead of calling Razorpay directly throughout the application.

## Why

It isolates:

- Authentication.
- HTTP behavior.
- API schemas.
- Error mapping.
- Retries.
- Provider-specific logic.

It also enables:

```text
RazorpayAdapter
SimulationAdapter
```

with the same domain-level interface.

---

# 10. Simulation Mode Is Mandatory

## Decision

Keep a deterministic simulation mode even when Razorpay Test Mode is integrated.

## Why

The build needs reliable metrics.

Simulation makes it possible to demonstrate:

- Large batches.
- Rare failures.
- Controlled failure injection.
- Reproducible metrics.
- Test coverage.
- Edge cases that are difficult to trigger on demand.

Simulation must not be presented as real Razorpay recovery. It must be clearly labelled.

---

# 11. Real Razorpay Test Mode Still Matters

## Decision

Simulation is not a substitute for provider integration.

At least one significant recovery path should use Razorpay Test Mode where feasible.

Recommended first real integration:

```text
failed/recoverable case
-> create Payment Link
-> observe payment/link lifecycle
-> receive webhook
-> verify payment
-> mark revenue recovered
```

## Why

A real provider integration demonstrates that the project is more than a local ML simulation.

---

# 12. Payment Links as a Primary Recovery Action

## Decision

Make Payment Link recovery one of the first real executable actions.

## Why

Razorpay documents Payment Links as a mechanism for collecting payment through a URL, with APIs to create, fetch, update, cancel, and resend links.

This provides a bounded and easy-to-explain recovery intervention:

```text
failed payment
-> determine that re-entry is appropriate
-> create Payment Link
-> track link
-> wait for actual payment
-> verify recovered revenue
```

## Rejected

### Automatically capture every authorized payment

Rejected as a recovery strategy.

Capture changes an already-authorized payment to captured state. It does not replace a failed customer payment attempt.

---

# 13. Webhooks + Reconciliation

## Decision

Use an event-driven architecture with periodic/fallback reconciliation.

## Why

A webhook indicates that provider state changed, but reliable financial systems should not treat event delivery as the only source of truth.

Use:

```text
Webhook
  -> persist
  -> process
  -> reconcile current provider state when needed
```

## Rejected

### Poll forever

Rejected because it is wasteful and less responsive.

### Trust webhooks blindly

Rejected because event delivery can be duplicated, delayed, or arrive in sequences where a current state lookup is useful.

---

# 14. Idempotency Is a First-Class Requirement

## Decision

Every consequential recovery action must have an idempotency key.

## Why

Agents and workers can retry. Networks can fail after the upstream server has processed a request. A second attempt must not create an unintended duplicate.

Store:

```text
idempotency_key
action_type
case_id
result
```

under a unique constraint.

---

# 15. Bounded State Machine Instead of Open-Ended Agent Loop

## Decision

Use an explicit recovery state machine.

## Why

Open-ended agent loops are difficult to debug and dangerous around money.

The recovery workflow should have known terminal states.

Recommended states:

```text
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

The agent can reason inside a state but cannot invent new financial states at runtime.

---

# 16. Event Store Is Not the Source of Truth for All Data

## Decision

Keep normalized tables and an audit/event log.

## Why

A normalized database makes current state efficient to query.

The audit trail gives historical explanation.

The two serve different purposes.

---

# 17. No Hidden Chain-of-Thought Storage

## Decision

Store structured reasoning metadata, not private chain-of-thought.

Store:

```json
{
  "decision": "CREATE_PAYMENT_LINK",
  "reason_code": "PAYMENT_METHOD_REENTRY",
  "evidence_ids": ["payment_123", "event_456"],
  "policy_checks": [
    "MAX_ATTEMPTS_PASSED",
    "AMOUNT_LIMIT_PASSED",
    "COOLDOWN_PASSED"
  ]
}
```

Do not store or expose the model's hidden internal reasoning.

---

# 18. Batch Metrics Over Cherry-Picked Examples

## Decision

Metrics must run over a complete deterministic batch.

## Why

The Razorpay track explicitly expects measured recovery across a batch.

The evaluation runner must record:

```text
amount at risk
amount recovered
recovery rate
attempts
escalations
failures
```

A single successful payment is not sufficient evidence.

---

# 19. Metrics Are Derived From Events

## Decision

Never manually enter recovered revenue.

`amount_recovered` must be derived from verified payment outcomes.

## Why

This prevents the demo from becoming a spreadsheet with a fake AI layer.

A recovery is counted only when the system can connect the successful payment outcome to the recovery case.

---

# 20. No Production Credentials

## Decision

The buildathon demo operates in Razorpay Test Mode.

## Why

This avoids production financial risk and keeps the repository safe to share.

Production secrets must never be committed.

---

# 21. No Over-Engineering

## Decision

Avoid microservices, Kubernetes, event buses, and multi-region deployment.

## Why

The project is being built by one person for a buildathon and hiring evaluation.

A modular monolith provides almost all of the engineering value with significantly lower implementation overhead.

Preferred deployment shape:

```text
Next.js
   |
FastAPI
   |
PostgreSQL
   |
optional Redis
```

---

# 22. Redis Is Optional

## Decision

Do not require Redis for the first MVP.

Introduce it only if asynchronous execution, distributed locks, or rate limiting actually requires it.

## Rejected

### Celery + Redis from day one

Rejected because it adds operational complexity before the workflow needs it.

---

# 23. No Generic "AI Customer Support" Layer

## Decision

Do not expand into a generic customer-support agent.

## Why

That dilutes the revenue-recovery proposition.

Customer communication exists only as an intervention within a measurable recovery workflow.

---

# 24. No Generic CRM

## Decision

Do not build:

- Contact management.
- Marketing automation.
- Full email campaign management.
- Sales CRM.

Only store enough customer context to make and audit recovery decisions.

---

# 25. Evaluation Philosophy

The technical reviewer should be able to answer "yes" to all of these:

```text
Does it solve a real merchant problem?
Does the agent actually take bounded actions?
Can I see why it acted?
Can I verify whether money was recovered?
Can I reproduce the metrics?
Can I trigger a failure?
Does it recover safely from the failure?
Can I understand the code?
Can I trust the system around financial actions?
```

The architecture must make those answers obvious from the repository and demo.
