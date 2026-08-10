# Migration Notes: 100% Free Model (2026-08-07)

Record of the change from paid (Go plan) to the 100% free model policy.

## Why

- The Go plan credit (`opencode-go/*`) was exhausted. Under the free model, there is no
  quota limit and therefore no rate-limit retry loop (a paid model that hits its limit
  leaves agents retrying the same call against the same exhausted model).

## Decision

- Make the free model the **primary**, not a fallback.
- The installed opencode **1.18.10 does not support native `fallbacks` /
  `cooldown_seconds` config** (that feature landed in a later release via PR). With no
  fallback chain available, the reliable fix is: primary = free.

## Files changed

| File | Change |
|------|--------|
| `opencode.json` (project) | `model` and `small_model` → `opencode/deepseek-v4-flash-free` |
| `~/.config/opencode/opencode.json` (global) | `model`, `small_model`, `agent.title.model` → `opencode/deepseek-v4-flash-free` |
| `agents/ai-orchestrator.md` | Removed PRO/FLASH routing; updated Vision policy to "vision deactivated, ask Owner before spending" |
| `agents/vision-agent.md` | Marked INATIVO; model → free; needs explicit approval to switch to `opencode-go/kimi-k3` |
| `docs/MODEL-POLICY.md` | Rewritten to 100% free + PLAN/BUILD mode routing |
| `README.md`, `docs/INSTALL.md`, `CONTRIBUTING.md` | Updated model references to free |

## Vision caveat

No free model has vision. Vision is therefore **deactivated**. When the Owner references
an image, the orchestrator must state vision is off and ask for explicit approval before
routing to `vision-agent` (which needs the paid `opencode-go/kimi-k3`).

## Revert

To revert to the paid plan, restore `model`/`small_model` to
`opencode-go/deepseek-v4-pro` and `opencode-go/deepseek-v4-flash` in both configs, restore
the vision-agent model to `opencode-go/kimi-k3`, and restore the PRO/FLASH section of
`docs/MODEL-POLICY.md`.