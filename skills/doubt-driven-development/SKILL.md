---
name: doubt-driven-development
description: Adversarial review of in-flight decisions with fresh context — CLAIM, EXTRACT, DOUBT, RECONCILE. Use for high-stakes work, unfamiliar code, or when a confident output is cheaper to verify now than debug later.
---

# Doubt-Driven Development

Adversarial fresh-context review of every non-trivial decision in-flight. The goal is to
catch confident mistakes before they ship.

## When to use

- Stakes are high (production, security, irreversible)
- Working in unfamiliar code
- A confident output arrived too easily
- You're about to merge / deploy / sign off

## The loop

```
CLAIM    → what did we assert? (the decision, stated cleanly)
EXTRACT  → what is it grounded in? (code, doc, data — find the actual evidence)
DOUBT    → attack the claim: what would make it wrong?
RECONCILE → resolve: keep, fix, or abandon with a written reason
```

### 1. CLAIM
State the decision as a falsifiable claim. "The migration is safe" → "The migration is safe
because the new index is used by all queries that were using the old one."

### 2. EXTRACT
Go to the ground truth. Read the actual code/config/data. Not the summary — the source.

### 3. DOUBT
Attack systematically:
- **Fresh eyes**: review the diff with no context. What breaks?
- **Edge cases**: empty input, null, boundary, concurrency, error path
- **Reverse test**: what would prove this WRONG? Run it.
- **Unfamiliarity check**: did we assume something about a library/API we haven't verified?
- **The reviewer's question**: "would a staff engineer approve this?" — if unsure, no.

### 4. RECONCILE
- Claim holds → record the evidence, proceed
- Claim broken → fix or abandon, write why
- Unknown → verify before shipping. Unknown is not "probably fine".

## Anti-rationalization

| Rationalization | Rebuttal |
|-----------------|----------|
| "It's probably fine" | Prove it or don't ship it |
| "We tested the happy path" | Test the failure path |
| "This is how it's always done" | Chesterton's Fence: find out WHY before assuming it's right |
| "The tests passed" | Do the tests test the thing you doubt? |
| "No time to check" | Cheaper to verify now than debug in prod |

## Verification

- Every non-trivial claim went through CLAIM→EXTRACT→DOUBT→RECONCILE
- Unknowns are listed as blockers, not silently assumed
- The diff was reviewed with fresh eyes
- The reverse test was run
