# Requirements and Features

## Product Scope

RevenuePilot is a solo-buildathon submission for Razorpay's **AI Revenue Recovery** track.

The first milestone is a convincing, reproducible demo using Razorpay Test Mode APIs where practical, supplemented by a deterministic simulation layer for scenarios that are difficult to generate reliably in Test Mode.

The product should operate in two modes:

1. **Razorpay Test Mode** for real API/webhook integration.
2. **Simulation Mode** for controlled batch evaluation and deterministic demonstration of edge cases.

Simulation Mode is mandatory because the buildathon requires measured batch-level recovery evidence and because relying entirely on live timing or manually triggered payment events makes evaluation fragile.

---

## Core Features

### F1. Merchant Workspace

Provide a single merchant dashboard with:

- Revenue at risk.
- Recovered revenue.
- Recovery rate.
- Active recovery cases.
- Pending actions.
- Escalated cases.
- Failed agent actions.
- Recent recovered transactions.
- Batch evaluation summary.

The dashboard is an operations console, not a generic analytics dashboard.

### F2. Transaction Ingestion

Ingest:

- Razorpay payment data.
- Razorpay order data.
- Payment failure events.
- Payment captured events.
- Relevant subscription/payment-link signals where supported.
- Simulation events.

Normalize external entities into internal records.

The application must retain the original Razorpay identifiers.

### F3. Revenue-at-Risk Detection

Identify cases using explicit rules.

Initial supported case types:

- Failed payment.
- Repeated payment failure.
- Abandoned/unfinished checkout represented by an internal simulation signal.
- Failed recurring payment represented through subscription-related events where available.
- Expired or unresolved payment-recovery opportunity.

Every candidate must store:

- Amount at risk.
- Currency.
- Customer identifier.
- Original event.
- Current state.
- Detection reason.
- Detection timestamp.
- Eligibility state.

### F4. Failure Diagnosis

Determine an actionable failure category.

Initial categories:

- `TRANSIENT_GATEWAY_FAILURE`
- `CUSTOMER_ACTION_REQUIRED`
- `PAYMENT_METHOD_FAILURE`
- `INSUFFICIENT_FUNDS`
- `EXPIRED_PAYMENT_METHOD`
- `BANK_DECLINE`
- `UNKNOWN_PAYMENT_FAILURE`
- `NON_RECOVERABLE`
- `ALREADY_RECOVERED`

Diagnosis should use deterministic Razorpay/payment fields first.

An LLM may be used to interpret ambiguous failure descriptions or produce explanations, but its output must not directly authorize tool execution.

### F5. Recovery Eligibility Engine

Before any action is taken, evaluate:

- Transaction state.
- Previous recovery attempts.
- Maximum retry count.
- Minimum time since previous attempt.
- Amount thresholds.
- Case type.
- Current payment status.
- Whether another action is already pending.
- Whether the action is allowed for the specific case.
- Whether the case has already reached a terminal state.

The eligibility engine must be deterministic.

### F6. Recovery Strategy Selection

Initial allowed strategy set:

- `RETRY_PAYMENT`
- `CREATE_PAYMENT_LINK`
- `RESEND_PAYMENT_LINK`
- `SCHEDULE_RETRY`
- `SEND_RECOVERY_PROMPT`
- `ESCALATE_TO_HUMAN`
- `STOP_RECOVERY`

The build should start with no more than 3 executable action types in the demo. Recommended minimum:

1. Create/resend payment link.
2. Schedule or perform a bounded retry/simulation retry.
3. Escalate.

Do not implement every possible recovery path just to increase feature count.

### F7. Recovery Action Execution

Every action must pass through a tool gateway.

The gateway is responsible for:

- Schema validation.
- Policy validation.
- Idempotency.
- Action logging.
- Timeout handling.
- Retry policy.
- API response normalization.
- Terminal-state detection.

The LLM must never directly call Razorpay.

### F8. Payment Link Recovery

Where appropriate, create a Razorpay Payment Link through the API.

The link must be associated with:

- Internal recovery case.
- Original order/payment identifier.
- Customer.
- Amount.
- Recovery attempt.

The link should be tracked until paid, cancelled, or expired.

Razorpay documents Payment Links as URLs that can be sent to customers and provides create/fetch/update/cancel/resend APIs.

### F9. Event and Webhook Processing

Expose a public webhook endpoint for Razorpay events.

Requirements:

- Verify `X-Razorpay-Signature`.
- Persist the raw event.
- Deduplicate events.
- Process state transitions idempotently.
- Preserve event ordering information where available.
- Reconcile event state with current API state if an event is ambiguous.

Razorpay explicitly documents webhook signature validation and notes the importance of idempotency and event ordering.

### F10. Outcome Verification

A recovery attempt is not considered successful because an API action succeeded.

Example:

`payment_link_created != revenue_recovered`

The system must wait for or query evidence of an actual successful payment.

Recovery success requires a terminal financial event such as:

- `payment.captured`.
- `order.paid`.
- Another verified transaction state supported by the selected integration.

The exact mapping must be implemented from current Razorpay documentation.

### F11. Agent Audit Trail

For each recovery case, show a timeline:

1. Detection.
2. Diagnosis.
3. Eligibility decision.
4. Selected strategy.
5. Policy checks.
6. Tool call.
7. API result.
8. Follow-up event.
9. Verification result.
10. Final state.

Do not expose hidden chain-of-thought.

Store structured decision metadata, for example:

- `decision`
- `reason_code`
- `evidence_ids`
- `policy_checks`
- `tool_name`
- `tool_arguments_hash`
- `outcome`

### F12. Human Escalation

Cases must be escalated when:

- Recovery budget is exhausted.
- The diagnosis is uncertain.
- The amount exceeds configured threshold.
- Multiple conflicting signals exist.
- The action requires human approval.
- The system detects an unsupported state.

Escalation is a successful safety outcome, not an agent failure.

### F13. Failure Recovery

At least one controlled failure scenario must be demonstrated.

Required behavior:

- Detect tool/API failure.
- Classify it as retryable or terminal.
- Apply bounded retry policy.
- Avoid duplicate action.
- Escalate or stop when the retry budget is exhausted.
- Log the failure and recovery.

### F14. Batch Evaluation

Provide a reproducible batch runner.

Input:

- Synthetic transactions/events.
- Optional Razorpay Test Mode dataset.

Output:

- Total cases.
- Eligible cases.
- Actions selected.
- Actions executed.
- Successful recoveries.
- Amount at risk.
- Amount recovered.
- Recovery rate.
- Average attempts per recovered case.
- Escalations.
- Terminal failures.
- Action-level metrics.

The batch should be sufficiently large to make the metric meaningful. Target at least 100 synthetic cases for local evaluation, even though Razorpay Track 3's stated requirement is measured recovery across a batch.

### F15. Scenario Generator

Generate deterministic synthetic cases with configurable distribution.

Example scenarios:

- 25% transient failures.
- 20% insufficient funds.
- 15% payment-method issues.
- 10% bank declines.
- 10% abandoned checkout.
- 10% already recovered.
- 5% terminal/non-recoverable.
- 5% ambiguous.
- 5% injected API/tool failure.

These exact percentages are defaults for testing and may be changed. The generator must seed randomness for reproducibility.

### F16. Agent Event Log

Persist all agent execution events.

Suggested event types:

- `CASE_DETECTED`
- `CASE_DIAGNOSED`
- `ACTION_PROPOSED`
- `ACTION_BLOCKED`
- `ACTION_EXECUTED`
- `ACTION_FAILED`
- `PAYMENT_RECONCILED`
- `RECOVERY_VERIFIED`
- `CASE_ESCALATED`
- `CASE_STOPPED`

### F17. Merchant Controls

Provide configurable safety parameters:

- Max attempts per case.
- Retry cooldown.
- Maximum automated recovery amount.
- Allowed action types.
- Human approval threshold.
- Escalation threshold.
- Model selection.
- Simulation/test mode.

Changing these parameters should be explicit and auditable.

---

## User Stories

### Merchant

> As a merchant, I want to see how much revenue is currently at risk so that I know where recovery effort should be focused.

> As a merchant, I want the system to explain why a payment failed so that recovery actions are targeted rather than generic.

> As a merchant, I want the system to take bounded recovery actions automatically so that recoverable revenue does not depend on manual follow-up.

> As a merchant, I want every action to be visible in an audit trail so that I can trust what the agent did.

> As a merchant, I want the system to stop after defined limits so that an automated recovery agent cannot repeatedly disturb customers or create uncontrolled API activity.

### Evaluator

> As an evaluator, I want to run a reproducible batch so that reported recovery metrics can be independently verified.

> As an evaluator, I want to inspect successful and failed cases so that I can judge the quality of the agent rather than the quality of the UI alone.

> As an evaluator, I want to see where AI is used and where deterministic logic is used so that I can evaluate the builder's AI judgment.

> As an evaluator, I want to intentionally trigger a failure and see graceful recovery so that I can judge engineering maturity.

---

## Constraints

### Build Format

- Solo builder.
- Public GitHub repository.
- 5-minute pitch video.
- The project must be runnable and understandable from the repository.
- Shortlisted builders proceed to a Razorpay panel.

### Payment Environment

Use Razorpay **Test Mode** only for the buildathon demonstration unless Razorpay explicitly authorizes another environment.

Do not store or hard-code production credentials.

### Budget

Assume a minimal/no-cost development budget.

Design so the core demo can run locally.

External paid infrastructure must not be a hard dependency.

### AI Cost Constraint

Do not send every transaction or every event to an external LLM.

AI inference should be reserved for tasks where it provides material value.

The system must remain operational in deterministic simulation mode without an external LLM.

### Platform

Preferred architecture:

- Browser-based frontend.
- Python backend.
- PostgreSQL database.
- Local Docker development.
- Razorpay REST APIs/webhooks.
- Optional local LLM or low-cost external LLM behind an abstraction.

The backend must own all secrets and external API calls.

### Timeline

The screenshots provide the application format and internship details but do not specify the exact hackathon build window in the supplied material. Therefore no exact number of build hours should be assumed in the implementation plan.

The architecture should support an MVP-first implementation where the following work before optional features:

1. Batch simulator.
2. Recovery-case model.
3. Policy engine.
4. One real Razorpay recovery action.
5. Webhook processing.
6. Recovery verification.
7. Metrics.
8. Audit trail.
9. Failure scenario.
10. Polished dashboard.

---

## MVP Boundary

The MVP is complete when the following can be demonstrated end-to-end:

`synthetic failed payment -> detection -> diagnosis -> bounded recovery decision -> Razorpay/Test Mode action or simulated equivalent -> success/failure event -> verification -> recovered amount metric -> audit trail`

Anything that does not strengthen this path should be considered secondary.

## Explicit Safety Requirements

- No arbitrary tool execution by the LLM.
- No autonomous production money movement.
- No infinite retries.
- No duplicate recovery actions.
- No silent action failure.
- No fabricated recovery metrics.
- No hidden manual intervention presented as autonomous behavior.
