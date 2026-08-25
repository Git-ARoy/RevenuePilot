# Project Overview

## Project Name

**RevenuePilot**  
Working name. Final branding is not fixed.

## One-Line Definition

RevenuePilot is an AI-assisted revenue recovery agent for Razorpay merchants that detects revenue at risk, diagnoses why the revenue is at risk, selects a permitted recovery intervention, executes that intervention through bounded tools, verifies the outcome, and stops according to explicit policies.

## Problem

Revenue loss frequently occurs after a customer has already demonstrated purchase intent. Examples include:

- A payment attempt fails.
- A customer abandons checkout.
- A recurring subscription charge fails.
- A mandate retry needs to be scheduled.
- A receivable becomes overdue.
- A merchant repeatedly retries an action that is unlikely to succeed.

The merchant typically has the transaction data but not a system that can continuously close the loop from:

`revenue at risk -> root cause -> recovery decision -> execution -> verification -> stopping condition`

The project must therefore solve more than detection. It must demonstrate measurable recovery of money or simulated merchant revenue on a controlled test batch.

## Target Users

### Primary User: Merchant / Merchant Operations Team

A small or mid-sized merchant uses the system to:

- View revenue currently at risk.
- Understand why individual payments or payment cohorts are failing.
- See the recovery action selected by the agent.
- Approve or configure bounded actions.
- Monitor recovered versus unrecovered revenue.
- Inspect every agent decision and tool call.
- Understand failures and escalations.

### Secondary User: Engineering / Risk / Finance Reviewer

A reviewer needs to verify that:

- Money-moving actions are bounded.
- The agent cannot enter an uncontrolled retry loop.
- Every consequential action is auditable.
- Metrics are reproducible.
- Failures are handled rather than hidden.
- AI is used selectively rather than replacing deterministic financial logic.

## Background and Motivation

This project is being built for Razorpay's solo buildathon, Track 3: **AI Revenue Recovery**.

The track asks for an agent that detects revenue at risk, determines an appropriate intervention, and executes a bounded recovery workflow. Examples given by Razorpay include payment failures, checkout abandonment, failed subscriptions, B2B receivables, mandate retries, Hinglish voice recovery, and promise-to-pay tracking.

The stated evaluation bar is explicitly outcome-oriented: the submission should show measured money recovered across a batch, compliant escalation, stopping rules, and an audit trail.

Razorpay's application material also says the build is evaluated on:

- Problem taste.
- Build quality.
- AI judgment.
- Failure recovery.

Therefore this project should be engineered as a compact production-style system rather than as an LLM demo.

## Product Thesis

A useful revenue recovery agent should not blindly retry failed payments or send generic messages.

It should answer five questions for every recoverable case:

1. **What happened?**
2. **Why did it happen?**
3. **Is recovery appropriate?**
4. **What is the safest permitted intervention?**
5. **Did the intervention recover the revenue, and should the agent continue or stop?**

The system should optimize for measurable recovered revenue while minimizing unnecessary interventions and false-positive actions.

## High-Level Goals

### Goal 1: Detect revenue at risk

Normalize payment and order events into a recoverable-case model and identify transactions that have an outstanding monetary opportunity.

### Goal 2: Diagnose the cause

Classify failures into actionable categories using deterministic fields first and AI only where ambiguity or unstructured explanation is involved.

### Goal 3: Select an intervention

Choose from a finite set of approved recovery actions based on transaction state, customer context, prior attempts, cooldowns, and recovery probability.

### Goal 4: Execute safely

Execute only actions allowed by policy. Every action must have preconditions, a maximum retry budget, idempotency protection, and a terminal state.

### Goal 5: Verify outcomes

Correlate subsequent Razorpay events or simulation events with the original recovery attempt and determine whether money was actually recovered.

### Goal 6: Produce measurable evidence

Run against a fixed test/simulation batch and report:

- Total revenue at risk.
- Total eligible cases.
- Total recovery attempts.
- Total successful recoveries.
- Amount recovered.
- Recovery rate.
- Recovery value rate.
- Action-level performance.
- Failure rate.
- Escalation rate.
- False/poor intervention cost where measurable.

### Goal 7: Make engineering judgment visible

Keep deterministic payment-state and safety logic separate from probabilistic/LLM reasoning. The architecture should make it obvious where AI is useful and where it would be irresponsible.

## Non-Goals

The first version must not attempt to become a full merchant CRM, payment gateway replacement, fraud platform, accounting platform, or general-purpose autonomous finance employee.

Specifically out of scope unless explicitly required later:

- Live production money movement.
- Arbitrary refunds.
- Unlimited automated customer messaging.
- Autonomous changes to merchant pricing.
- Autonomous account configuration changes.
- Autonomous deletion of financial records.
- Unbounded LLM tool access.
- Generic chatbot functionality unrelated to recovery.
- Building a complete communications infrastructure.
- Supporting every Razorpay product.
- Production-grade multi-tenant billing for the demo.

## Operating Principle

**The agent proposes and executes only bounded recovery actions. It never gets unrestricted authority over money.**

A deterministic policy engine remains the final gate before consequential actions.

## Buildathon Positioning

The product should be presented as:

> **An agent that closes the revenue-recovery loop, not a model that predicts failed payments.**

The demonstration should include one successful recovery batch and at least one intentionally induced failure showing:

- Detection.
- Decision.
- Tool execution.
- Failure.
- Recovery / retry handling.
- Audit logging.
- Final metric update.

## Success Criterion

The project is successful when a reviewer can run the public repository, execute a reproducible test batch, inspect the agent's decisions, observe bounded actions, and verify that the reported recovered amount comes from recorded transaction outcomes rather than manually fabricated metrics.

## External API Context

Razorpay's public API documentation currently exposes REST APIs under `https://api.razorpay.com/v1` for most resources. Payment APIs include fetching payments and capturing authorized payments; Orders APIs support creating and retrieving orders and retrieving payments associated with an order. Payment Links APIs support creating, fetching, updating, cancelling, and resending payment links. Razorpay also exposes webhook events for payment state changes.

Relevant references:

- https://razorpay.com/docs/api/
- https://razorpay.com/docs/api/payments/
- https://razorpay.com/docs/api/orders/
- https://razorpay.com/docs/api/payments/payment-links/
- https://razorpay.com/docs/webhooks/payments/

These external API contracts must be treated as integration dependencies and verified against the current Razorpay documentation before implementation.
