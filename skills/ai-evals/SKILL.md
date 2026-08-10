---
name: ai-evals
description: "Build and run evaluations for LLM prompts, agents, and RAG: golden sets, assertions, regression gates, CI integration. Use before changing any prompt or agent, and to prevent regressions."
---

# AI Evals

Treat evals as the unit tests of AI development. Define expected behavior before implementing,
run continuously, track regressions with every change.

## Principles

1. **Golden set first**, fixed inputs + expected outputs, frozen (versioned).
2. **Assert, don't judge**, deterministic assertions over LLM-as-judge wherever possible.
3. **Regression gate**, a prompt/agent change that fails the golden set does not ship.
4. **Pass@k**, reliability under sampling, not one lucky run.

## Golden set structure

```json
{
  "id": "GS-1",
  "type": "factual | current-events | false-premise | osint | comparative",
  "input": "...",
  "expected": { "answer": "...", "mustContain": ["..."], "mustNotContain": ["..."] },
  "knownTraps": ["hallucinate version", "HIGH on single source"]
}
```

## Eval types

| Type | Purpose |
|------|---------|
| Capability | Can it do something new? |
| Regression | Does it still do what it used to? |
| Robustness | Adversarial inputs, edge cases, false premises |
| Stability | Same input K times, where does output fluctuate? |

## Assertions

- **Exact match**, normalized answer equals key (factual items)
- **Contains / not-contains**, presence of required elements, absence of banned ones
- **Schema valid**, output parses, required fields present
- **URL liveness**, cited URLs resolve (research)
- **Fabrication kill-check**, banned specifics absent (false-premise items)
- **Contract lint**, required headers, length budget, zero preamble

## Regression flow

1. Change a prompt/agent
2. Run the full golden set (N≥3 runs for stability)
3. Compare vs baseline: no regressions on automatable dims
4. Report per-item deltas, not just the mean
5. Promote only if it passes the gate

## CI integration

- Run evals on every prompt change (in CI or pre-commit).
- Keep baselines versioned. A baseline IS the contract.
- Do not publish the answer key with the eval harness if it would contaminate the benchmark.

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| LLM-judge-only | Deterministic assertions first |
| Edit golden set freely | Freeze + version; edit = new version |
| One run, pass | N≥3, report variance |
| Mean-only reporting | Per-item deltas |
| Change prompt without eval | Regression gate blocks the change |

## Verification

- Golden set is frozen and versioned
- Every change ran the full suite
- No regressions on automatable dims
- Fabrication kill-checks pass on adversarial items
