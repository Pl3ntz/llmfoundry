---
description: Build and run evals for a prompt, agent, or LLM feature
model: opencode-go/deepseek-v4-flash
agent: ai-evals-runner
---

Build and run evaluations using the `ai-evals` skill.

**Subject under eval:** {{argument}}

1. Define a frozen golden set (include factual, false-premise, adversarial, and edge cases)
2. Write deterministic assertions (not LLM-judge where avoidable)
3. Run N≥3 for stability, report per-item deltas vs baseline
4. Write artifacts to `evals/<name>/` (golden-set.json, baseline.json)
5. Report promote/block with evidence
