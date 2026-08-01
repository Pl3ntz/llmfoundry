# Model Policy — Why DeepSeek

LLMFoundry is built around the **DeepSeek family**. This is a deliberate, measured cost
decision.

## The decision

| Role | Model | Requests/mo | Cost/MTok in | Cost/MTok out |
|------|-------|-------------|--------------|---------------|
| Default | `opencode-go/deepseek-v4-pro` | 17,150 | $0.435 | $0.87 |
| small_model | `opencode-go/deepseek-v4-flash` | 158,150 | $0.14 | $0.28 |

Compared to the most expensive option in the Go plan:

| Model | Out $/MTok | Requests/mo | vs DeepSeek Flash |
|-------|-----------|-------------|-------------------|
| **DeepSeek V4 Flash** | $0.28 | 158,150 | — |
| **DeepSeek V4 Pro** | $0.87 | 17,150 | 11x cheaper than kimi-k3 |
| Kimi K3 | $15.00 | 490 | **53x more expensive** |
| GLM-5.2 | $4.40 | 4,300 | 15x more expensive |

## Why it matters

- Same $10/mo Go plan → DeepSeek Flash yields **158k requests** vs Kimi K3's **490**
  (322x more work for the same price).
- DeepSeek V4 Pro has **0-day data retention** (doesn't train on your code).
- Native 1M context, 384K max output, thinking mode, tool calls, JSON output.

## Rules for agents

1. Every agent/command uses `opencode-go/*` — never `opencode/` (Zen) to avoid spending
   Zen balance, never expensive models (kimi/grok/glm) unless explicitly requested.
2. `small_model` (flash) for evals, reformulation, and mechanical tasks.
3. Parametric memory is stale — versions/APIs must be live-verified.
