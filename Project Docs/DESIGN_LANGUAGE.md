# RevenuePilot Design Language

## Purpose

This document defines the visual and interaction language for RevenuePilot.

RevenuePilot is a financial operations product for merchants. The interface must feel like a serious financial infrastructure product, not an AI toy, generic SaaS dashboard, or marketing website.

The visual system should communicate:

- Trust
- Precision
- Financial clarity
- Operational control
- Technical sophistication
- Calmness under failure
- AI-assisted intelligence without excessive AI theatrics

The frontend should feel credible enough that a Razorpay engineering/product reviewer could imagine this becoming a real internal or merchant-facing product.

---

# 1. Design Direction

## Core Aesthetic

**Modern financial infrastructure + intelligent operations console.**

The design should sit between:

- Razorpay-like fintech clarity
- Linear-like product polish
- Stripe-like financial information density
- Modern AI tooling
- Enterprise operations software

Do NOT make it look like:

- A generic admin dashboard
- A crypto dashboard
- A futuristic cyberpunk AI interface
- A neon AI startup landing page
- A template-generated SaaS dashboard
- A chatbot application

The product should look engineered rather than decorated.

---

# 2. Primary Design Principle

## "Financial clarity first, AI second."

The user should immediately understand:

1. How much revenue is at risk.
2. How much has been recovered.
3. What the agent is currently doing.
4. Why the agent made a decision.
5. What requires human attention.

The AI should be visible through behavior and explanations, not through excessive visual effects.

Avoid labels such as:

> "AI MAGIC"

> "Powered by AI"

> "Autonomous Super Agent"

Prefer precise language:

> "Recovery recommendation"

> "Automated recovery"

> "Agent decision"

> "Policy approved"

> "Awaiting payment"

---

# 3. Visual Personality

The interface should feel:

- Dense but not crowded
- Minimal but not empty
- Premium but not ornamental
- Technical but accessible
- Data-rich but highly hierarchical
- Calm during normal operation
- Visually explicit during exceptions

Use whitespace strategically.

Do not create excessive empty hero sections inside the dashboard.

---

# 4. Color System

## Base

Use a warm-neutral/light financial interface as the primary theme.

Suggested foundation:

```text
Background:
#FAFAF9

Surface:
#FFFFFF

Elevated Surface:
#FFFFFF

Primary Text:
#171717

Secondary Text:
#737373

Muted Text:
#A3A3A3

Border:
#E5E5E5

Subtle Border:
#F0F0F0
```

The exact values can be adjusted by the implementation, but the visual result should remain close to this range.

---

## Primary Accent

Use a restrained Razorpay-inspired blue as the primary interaction accent.

Suggested:

```text
Primary:
#0D6EFD

Primary Hover:
#0958D9

Primary Soft:
#EAF2FF
```

Do not flood the interface with blue.

Blue should primarily indicate:

- Interactive controls
- Selected navigation
- Links
- Primary CTA
- Agent activity
- Focus states

---

# 5. Semantic Colors

Semantic colors must communicate operational state consistently.

## Success

Use green for:

- Payment recovered
- Successful action
- Verified recovery
- Positive revenue outcome

Suggested:

```text
Success:
#16A34A

Success Soft:
#ECFDF3
```

## Warning

Use amber for:

- Pending recovery
- Waiting for customer
- Retry scheduled
- Attention required

```text
Warning:
#D97706

Warning Soft:
#FFF7E6
```

## Error

Use red only for:

- Failed payment
- Failed tool execution
- Policy violation
- Terminal recovery failure

```text
Error:
#DC2626

Error Soft:
#FEF2F2
```

## Neutral

Use neutral gray for:

- Stopped
- Informational
- Historical
- Disabled

---

# 6. Avoid Color Overuse

Do not make every card colorful.

BAD:

```text
[green card] [blue card] [purple card] [orange card]
```

GOOD:

```text
Mostly neutral dashboard

Amount at risk        ₹10.4L
Amount recovered      ₹3.8L
Recovery rate         37.1%

Small semantic indicators provide state.
```

Color should carry meaning.

If everything has a color, nothing has meaning.

---

# 7. Typography

Use a modern sans-serif font.

Preferred:

```text
Inter
```

If unavailable, use:

```text
system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

Typography should prioritize numerical readability.

---

# 8. Type Scale

## Page Title

```text
28-32px
font-weight: 600
letter-spacing: -0.02em
```

## Section Heading

```text
18-20px
font-weight: 600
```

## Card Heading

```text
14-16px
font-weight: 600
```

## Body

```text
14px
font-weight: 400
line-height: 1.5
```

## Secondary

```text
13px
color: muted
```

## Financial Metric

Large monetary figures should be visually dominant.

Example:

```text
₹10.42L
```

Use:

```text
28-36px
font-weight: 600
letter-spacing: -0.03em
```

Do not use excessively large 64-96px dashboard numbers.

---

# 9. Numbers

Financial numbers are first-class UI elements.

Prefer:

```text
₹10.42L
```

over:

```text
10,42,500 INR
```

in primary dashboard views.

However, detail views should show the exact amount:

```text
₹10,42,500.00
```

Always display the currency.

Do not use ambiguous values such as:

```text
10.42
```

without context.

---

# 10. Layout

## Application Shell

Use a two-level structure:

```text
┌──────────────────────────────────────────────────────┐
│ Top Bar                                              │
├───────────────┬──────────────────────────────────────┤
│               │                                      │
│ Sidebar       │ Main Content                         │
│               │                                      │
│ Dashboard     │                                      │
│ Recovery      │                                      │
│ Transactions  │                                      │
│ Agent         │                                      │
│ Evaluation    │                                      │
│ Settings      │                                      │
│               │                                      │
└───────────────┴──────────────────────────────────────┘
```

Sidebar should be compact.

Do not make the sidebar dominate the page.

---

# 11. Sidebar

Navigation:

```text
RevenuePilot

Overview

Recovery
  Active
  Recovered
  Escalated

Transactions

Agent Activity

Evaluation

Settings
```

The selected item should use:

- Soft blue background
- Blue text/icon
- Subtle radius

Avoid large pill-shaped navigation elements.

---

# 12. Top Bar

The top bar should contain:

Left:

```text
Current page title / breadcrumb
```

Right:

```text
Test Mode
Merchant status
Profile
```

Test Mode should be extremely clear.

Example:

```text
● TEST MODE
```

Use a subtle amber indicator.

Never make the UI look like it is connected to production when it is not.

---

# 13. Dashboard

The dashboard should answer the most important business questions immediately.

Recommended top section:

```text
Revenue Recovery

Recover more revenue from failed payments
without increasing manual operations.

[Run evaluation] [View active cases]
```

Then:

```text
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ Revenue at     │ │ Recovered      │ │ Recovery rate  │
│ risk           │ │                │ │                │
│ ₹10.42L        │ │ ₹3.87L         │ │ 37.1%          │
└────────────────┘ └────────────────┘ └────────────────┘
```

Then:

```text
Recovery performance
──────────────────────────────────────

Recovered revenue over time
```

Then:

```text
Active recovery cases
──────────────────────────────────────

Case       Amount     Reason       Action       Status
```

---

# 14. Dashboard Hierarchy

The hierarchy must be:

```text
Business outcome
      ↓
Operational status
      ↓
Agent decisions
      ↓
Individual cases
      ↓
Technical details
```

Do not start the dashboard with:

```text
LLM tokens
Model latency
Prompt count
Tool calls
```

Those are secondary engineering metrics.

---

# 15. Recovery Case Page

This is one of the most important screens.

It should feel like an investigation workspace.

Example:

```text
← Recovery Cases

Payment #pay_123

₹49,900
FAILED PAYMENT

Customer
Rahul Sharma
rahul@example.com

────────────────────────────────

Why this case is recoverable

Transient payment failure detected.
One recovery attempt remains.

────────────────────────────────

Recovery decision

CREATE PAYMENT LINK

Recovery score
81%

Policy
✓ Amount limit
✓ Retry budget
✓ Cooldown
✓ Action allowed

[Execute recovery]
```

Then:

```text
Activity

10:31  Case detected
10:32  Failure diagnosed
10:32  Recovery recommended
10:32  Policy approved
10:33  Payment link created
10:38  Payment received
10:38  Recovery verified
```

---

# 16. Agent Activity

The agent should not look like a chatbot.

Do NOT use a chat bubble interface as the primary agent visualization.

Instead use a structured event stream:

```text
Agent Activity

● CASE_DETECTED
  Payment failed
  ₹49,900

● DIAGNOSIS_COMPLETE
  CUSTOMER_ACTION_REQUIRED
  Confidence: 91%

● POLICY_APPROVED
  CREATE_PAYMENT_LINK

● ACTION_EXECUTED
  Payment link created

● RECOVERY_VERIFIED
  ₹49,900 recovered
```

This communicates autonomous behavior without pretending the system is having a conversation.

---

# 17. AI Reasoning Display

Never display raw chain-of-thought.

Instead show:

```text
Decision rationale

Failure reason indicates the customer may
complete payment using a fresh payment attempt.

Evidence
• Payment failed
• One previous attempt
• Recovery window active

Decision
Create Payment Link
```

The UI should expose decision evidence, not hidden model reasoning.

---

# 18. Policy Gate Visualization

The Policy Engine is a major differentiator and should be visible.

Use a compact checklist:

```text
Policy Check

✓ Case eligible
✓ Amount within limit
✓ Retry budget available
✓ Cooldown satisfied
✓ Action enabled
✓ No concurrent attempt

ACTION APPROVED
```

For blocked actions:

```text
✕ Retry budget exhausted

ACTION BLOCKED
Escalate to merchant
```

This should be visually clear without looking like a security console.

---

# 19. Recovery Timeline

Use a vertical timeline.

Example:

```text
● Recovery verified
│   ₹49,900 recovered
│
● Payment link created
│   Link sent to customer
│
● Policy approved
│   Retry budget: 1/2
│
● Diagnosis
│   Customer action required
│
● Payment failed
    ₹49,900
```

Each event should include:

- Timestamp
- Event type
- Human-readable explanation
- Relevant metadata

---

# 20. Tables

Tables should be dense enough for operational use.

Columns should prioritize:

```text
Case
Amount
Reason
Recovery score
Action
Status
Updated
```

Do not display 15 columns by default.

Allow the user to enter the detail page for technical metadata.

---

# 21. Status Badges

Use compact badges.

Examples:

```text
RECOVERED
ACTION PENDING
WAITING
ESCALATED
FAILED
STOPPED
```

Badges should be:

- Small
- Medium-weight
- Slightly rounded
- Semantic

Avoid huge pill components.

---

# 22. Buttons

Primary buttons:

```text
Execute recovery
Run evaluation
Create payment link
```

Secondary:

```text
View case
Inspect decision
View audit trail
```

Danger:

```text
Stop recovery
```

Avoid exaggerated CTA language.

---

# 23. Cards

Cards should be used to establish hierarchy, not to wrap every piece of information.

Preferred:

- White surface
- 1px neutral border
- 10-14px radius
- Minimal shadow

Avoid:

- Heavy gradients
- Glassmorphism everywhere
- Excessive shadows
- Thick borders
- Decorative illustrations

---

# 24. Charts

Charts should answer business questions.

Useful charts:

### Recovery Value

```text
Recovered revenue vs revenue at risk
```

### Recovery Rate

```text
Recovery rate by intervention
```

### Failure Reasons

```text
Failed payments by reason
```

### Agent Outcomes

```text
Recovered
Escalated
Stopped
Failed
```

Avoid charts that exist only because a dashboard "needs a chart."

---

# 25. Evaluation Page

The Evaluation page is important for the buildathon demo.

It should clearly show:

```text
Batch Evaluation

100 cases
₹27.50L at risk
₹10.15L recovered
36.9% recovery rate

────────────────────────────────

Actions
Payment Link       42
Retry              21
Escalation          9

────────────────────────────────

Outcomes
Recovered           51
Unrecovered         36
Escalated            9
Failed               4
```

Include:

```text
Seed: 42
Mode: Simulation
```

so the evaluation is reproducible.

---

# 26. Simulation Mode

Simulation Mode should be visually distinct.

Use:

```text
SIMULATION
```

or:

```text
TEST MODE
```

Never make synthetic recovery metrics look identical to live merchant data without a clear mode indicator.

Recommended top-bar indicator:

```text
● SIMULATION
```

---

# 27. Motion

Motion should be subtle and functional.

Use animation for:

- Page transitions
- Loading states
- New recovery events
- Status changes
- Progress
- Expanding details

Avoid:

- Constant floating animations
- Large parallax
- Excessive particle effects
- Animated gradients
- AI "thinking" animations everywhere

The agent should feel fast and controlled.

---

# 28. Loading States

Do not use generic full-page spinners.

Prefer skeleton states.

For agent actions:

```text
Evaluating recovery policy...
```

Then:

```text
Policy approved
```

Keep operational feedback explicit.

---

# 29. Error States

Errors must explain:

1. What happened.
2. Whether money was affected.
3. What the system did.
4. What happens next.

Example:

```text
Recovery action failed

The Payment Link request timed out.
No duplicate action was created.

The agent will retry once after the
configured cooldown.

[View failure details]
```

Do not simply display:

```text
Something went wrong.
```

---

# 30. Empty States

Empty states should be useful.

Example:

```text
No active recovery cases

All currently detected opportunities
have been recovered, stopped, or escalated.
```

Avoid generic empty-state copy.

---

# 31. Forms

Forms should be compact and operational.

Use labels above inputs.

Do not rely on placeholders as labels.

For policy configuration:

```text
Maximum automated attempts
[ 2 ]

Recovery cooldown
[ 60 minutes ]

Maximum automated recovery amount
[ ₹10,000 ]

Human approval threshold
[ ₹5,000 ]
```

Show the consequences of changing a policy.

---

# 32. Settings

Settings should expose:

```text
Recovery Policies
AI Configuration
Razorpay Test Mode
Webhook Configuration
Simulation
```

Secrets should never be displayed.

Instead:

```text
Razorpay API
Connected

Key ID
rzp_test_••••••••••••

Secret
Configured
```

---

# 33. AI Configuration

The current local model should be shown clearly:

```text
AI Provider

Ollama

Model

Qwen3 8B

Status

● Connected
```

Do not make this screen look like an LLM playground.

The merchant does not need model tuning controls unless they are actually useful for the product.

---

# 34. Icons

Use a single icon system consistently.

Preferred:

**Lucide Icons**

Use icons for:

- Navigation
- Status
- Actions
- Information
- Settings

Do not use emojis as functional UI icons.

Avoid mixing multiple icon libraries.

---

# 35. Border Radius

Use a restrained radius system:

```text
Small controls: 6px
Cards: 10-12px
Large panels: 14px
```

Do not make every component extremely rounded.

Avoid excessive "bubble UI."

---

# 36. Shadows

Prefer borders over shadows.

Default cards:

```text
border: 1px solid #E5E5E5
box-shadow: none
```

Elevated overlays can use a subtle shadow.

The interface should feel like a financial application, not a neumorphic design system.

---

# 37. Responsive Behavior

Desktop is the primary target because the product is an operations dashboard.

Support:

- 1440px
- 1280px
- 1024px

At smaller widths:

- Collapse sidebar.
- Convert dense tables into cards.
- Stack KPI cards.
- Preserve critical financial information.

Do not simply shrink desktop layouts until they become unusable.

---

# 38. Accessibility

Minimum requirements:

- Keyboard navigation.
- Visible focus states.
- Semantic HTML.
- Accessible labels.
- Sufficient contrast.
- Do not communicate state using color alone.
- Buttons must have meaningful labels.
- Tables must have proper headers.

---

# 39. Frontend Engineering Rules

Use:

- TypeScript.
- Reusable components.
- Centralized design tokens.
- Consistent spacing.
- Shared status components.
- Shared typography primitives.
- Shared currency/number formatting.

Do not hard-code arbitrary colors throughout components.

Prefer semantic design tokens such as:

```text
text-primary
text-success
bg-surface
border-default
```

---

# 40. Design Tokens

Create centralized tokens for:

```text
colors
spacing
radius
typography
shadows
z-index
transitions
```

The exact implementation can use Tailwind configuration, CSS variables, or the project's component system.

---

# 41. Dark Mode

Dark mode is not a first-priority feature.

Do not spend significant development time on it before the primary light theme is polished.

If implemented later, it should retain the same semantic hierarchy and avoid pure black backgrounds.

---

# 42. Landing Page

If a landing page is built, it should be minimal.

Hero:

```text
Recover revenue.
Automatically.

RevenuePilot detects payment failures,
chooses bounded recovery actions,
and verifies the money recovered.

[View recovery dashboard]
[Run evaluation]
```

Then show the actual product.

Do not create generic AI-startup marketing copy.

The dashboard is the strongest proof of the product.

---

# 43. Product Voice

Use concise, operational language.

Prefer:

```text
Revenue recovered
```

over:

```text
You just recovered some money!
```

Prefer:

```text
Recovery action blocked
```

over:

```text
Oops! The AI couldn't do that.
```

Prefer:

```text
Payment verification pending
```

over:

```text
Waiting for magic to happen...
```

The interface should sound like financial infrastructure.

---

# 44. AI-Specific Visual Rule

AI should be represented through decision intelligence, not visual gimmicks.

Good:

```text
Recovery score: 81%

Recommended:
Create Payment Link

Evidence:
Payment failed once
Recovery window active
Customer action required
```

Bad:

```text
✨ AI AGENT THINKING... ✨
```

The product's intelligence should be self-evident from the workflow.

---

# 45. Demo Optimization

The frontend must be optimized for the 5-minute Razorpay buildathon presentation.

The evaluator should understand the product within approximately 20 seconds of seeing the dashboard.

The first viewport should communicate:

```text
What problem?
How much money?
How much recovered?
What is the agent doing?
What can I inspect?
```

Ideal demo sequence:

```text
Dashboard
   ↓
Select failed payment
   ↓
Show diagnosis
   ↓
Show policy checks
   ↓
Execute recovery
   ↓
Show webhook/event
   ↓
Show recovered amount
   ↓
Open audit timeline
   ↓
Run/inspect batch metrics
   ↓
Trigger failure scenario
   ↓
Show bounded retry/escalation
```

The UI should support this flow naturally.

---

# 46. What Not To Build

Do not add visual features simply because they make the product look "AI."

Do not use:

- Neon gradients
- AI avatars
- Robot illustrations
- Floating particles
- Fake terminal animations
- Chat-first UI
- Excessive glassmorphism
- Huge hero typography inside the dashboard
- Excessive rounded cards
- Decorative 3D graphics
- Fake real-time numbers
- Fake customer activity
- Fake recovery events

Every visual element should support product comprehension.

---

# 47. Final Design Test

Before considering the frontend complete, ask:

### Trust

Would a merchant trust this interface with payment recovery?

### Clarity

Can a user understand the current financial state in under 10 seconds?

### AI Judgment

Can the user see where AI contributed without seeing fake "AI magic"?

### Safety

Can the user understand why an action was allowed or blocked?

### Reliability

Can the user see failures and recovery instead of only successful paths?

### Product Quality

Does this look like a serious fintech product rather than a hackathon dashboard?

If any answer is "no", improve the interface before adding more features.

---

# Implementation Priority

Frontend implementation should prioritize, in this exact order:

1. Application shell and navigation.
2. Dashboard and primary recovery metrics.
3. Recovery case detail page.
4. Agent decision and policy visualization.
5. Audit/event timeline.
6. Evaluation page.
7. Simulation controls.
8. Settings and configuration.
9. Responsive refinement.
10. Secondary polish and motion.

Do not spend time on animations, dark mode, or a landing page before the core operations workflow is polished.
