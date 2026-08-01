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

## Routing: PRO vs FLASH (explicit policy)

The cost discipline lives in *which* model a task routes to. Flash is 3x cheaper and
9x more volume. The rule: **reasoning to PRO, mechanical to FLASH.**

| Task class | Model | Examples |
|------------|-------|----------|
| Deep reasoning / synthesis | **PRO** | research correlation, architecture design, security review, orchestration, code review, SPEC writing |
| Mechanical / high-volume / cheap | **FLASH** | evals, memory ops, reformulation, lookups, summarization, bash error capture |

### Routing table (what the orchestrator follows)

| When you... | Use |
|-------------|-----|
| orchestrate, delegate, synthesize, review security/architecture | PRO (you are PRO) |
| delegate deep research | deep-researcher = PRO |
| delegate evals | ai-evals-runner = FLASH |
| answer a single fact / lookup directly | **FLASH** (or small_model), never PRO |
| run memory ops (`/ai-memory`) | FLASH |
| do mechanical rewrite / paraphrase / extract | FLASH |
| write a SPEC, design, or high-stakes decision | PRO |

### Rules the orchestrator MUST follow

1. **Direct lookups never spend PRO.** A "what is X / syntax / version" question is
   answered with FLASH or the small_model — routing to deep-researcher for a fact is
   wasteful (and the routing table already forbids it).
2. **Delegation is already priced.** Subagent frontmatter fixes the model: deep-researcher,
   ai-architect, llm-security-reviewer = PRO; ai-evals-runner = FLASH. Do not override up.
3. **FLASH default for cheap work.** If a task is mechanical and you are unsure, FLASH.
   Upgrade to PRO only when reasoning depth is actually required.
4. **The `small_model` is the FLASH alias** for background/mechanical steps.

This is enforced implicitly by frontmatter + explicitly by this policy. A task that spends
PRO where FLASH suffices is a policy violation.
