# Model Policy: 100% Free

LLMFoundry runs entirely on the **free model** `opencode/deepseek-v4-flash-free`. This is a
deliberate decision to eliminate any dependency on paid quotas (the Go plan credit
previously used was exhausted). The free model has **no limit exhaustion and no loop on
rate-limit errors**, which is the guarantee that always matters.

## The decision

| Role | Model | Cost |
|------|-------|------|
| Default (`model`) | `opencode/deepseek-v4-flash-free` | **$0** |
| small_model | `opencode/deepseek-v4-flash-free` | **$0** |
| title model | `opencode/deepseek-v4-flash-free` | **$0** |

No paid model is used anywhere. The opencode 1.18.10 installed here does **not** support
native `fallbacks`/`cooldown_seconds` config (that PR landed later), so there is no
fallback chain to configure — the fix is making the free model the *primary*, not a
fallback. See `docs/migration-notes.md` for the migration record.

## Why it matters

- **Zero cost.** No request count, no $/MTok, no budget to track.
- **Zero loop.** A paid model that hits its limit leaves the agent retrying the same call
  against the same exhausted model. The free model has no limit, so the loop cannot exist.
- DeepSeek V4 has **0-day data retention** (doesn't train on your code), native 1M context,
  thinking mode, tool calls, JSON output.

## Rules for agents

1. Every agent/command uses `opencode/deepseek-v4-flash-free`. Never configure
   `opencode-go/*`, kimi, grok, or other paid/expensive models anywhere.
2. There is no PRO-vs-FLASH cost split anymore: everything is the same free model.
   Routing still matters for *mode* (PLAN vs BUILD), not for cost.
3. Parametric memory is stale, versions/APIs must be live-verified.

## Mode routing: PLAN vs BUILD

No model-cost dimension remains, so the only routing decision that matters is risk.

| Mode | Tools | Risk profile | Use for |
|------|-------|--------------|---------|
| **PLAN** | read-only (edit/bash = ask) | Zero writes, zero surprises | understanding, design, review, decision before action |
| **BUILD** | full tools | Writes, runs, changes state | implementation after a plan exists |

### The rule

**Ambiguity or stakes → PLAN first. Clear + approved → BUILD.**
Never BUILD something you don't understand. Never PLAN something already decided, that's
ceremony.
