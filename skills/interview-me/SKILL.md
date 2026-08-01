---
name: interview-me
description: Extract requirements one question at a time until ~95% confidence in what the user wants. Use when a request is underspecified, ambiguous, or high-stakes. Ask one question, wait for the answer, then the next.
---

# Interview Me

Extract what the user actually wants, not what they think they should want. One question
at a time. Stop only when you can state the requirements with ~95% confidence.

## When to use

- The ask is underspecified ("improve the agent", "make it better")
- The stakes are high (production, irreversible, public contract)
- Multiple valid interpretations exist
- The user says "interview me" or "grill me"

## Process

Ask ONE question. Wait for the answer. Then ask the next. Never batch all questions.

### Question order

1. **Outcome** — "What should be true when this is done?"
2. **Constraint** — "What must NOT change or break?"
3. **Scope** — "What is explicitly out of scope?"
4. **Users** — "Who uses this, and what do they need that they don't say?"
5. **Risk** — "What happens if this fails? What's the blast radius?"
6. **Measure** — "How do we know it worked? What's the metric?"

### Confidence check

After each answer, mentally update: can you state (a) outcome, (b) constraints, (c) scope,
(d) success metric? All four clear → you're at ~95%, stop and restate.

## Deliverable

Restate the full understanding as a SPEC (see `ai-dev-process`) and confirm.

## Rationalization check

| Excuse | Rebuttal |
|--------|----------|
| "I know what they mean" | The gap between intended and stated is where projects fail |
| "Asking annoys them" | One good question beats one wrong implementation |
| "I'll clarify during the work" | Clarify at $0 cost now, not at rework cost later |
