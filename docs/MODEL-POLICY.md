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
fallback chain to configure. The fix is making the free model the *primary*, not a
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

## Token economy (2026-08-10)

Baseline medido do `~/.local/share/opencode/opencode.db` (660 sessões, `scripts/cost-snapshot.sh`):
**325.7M tokens input, 6.3M output (2%), 3.53B cache_read, $61.96 histórico**. O gargalo é
INPUT + CACHE, não output. Qualquer otimização de tokens deve mirar input/cache.

Práticas adotadas (fazer mais com menos tokens, sem perder eficiência):

1. **Piso fixo por turno era ~18K tokens**: AGENTS.md global 1.4K + system prompt 2.9K +
   lista de 175 skills ~11.6K. Reduzido via AGENTS.md enxuto (544 tokens) e SkillReducer
   nas descrições dos 30 skills locais (12% corte). Os 145 skills globais ficam por
   SkillReducer em etapa separada (afetam outros projetos).
2. **Cache-friendly ordering**: contexto estável (AGENTS.md, system prompt, regras
   invariantes) deve ficar no PREFIXO do prompt. DeepSeek dá desconto de ~98% em cache
   hit; prefixo estável maximiza hits e reduz custo efetivo de cache_read em sessões longas.
3. **Reuso entre sessões**: deep-researcher persiste ledger na foundry-memory
   (pergunta → claims → gaps → fontes); missão nova consulta "onde paramos", não
   re-pesquisar o fechado (a maior economia real em valor absoluto).
4. **Sessões gigantes são redesign, não threshold**: loop de 2.250 turns (98M input,
   970M cache) é pipeline disfarçado. Deve virar subagentes com contexto isolado
   (só sumário volta) + compactação a 70-80% da janela, nunca resumo em prosa.
5. **Teto de iterações**: deep-researcher max 12 websearch + 8 webfetch; estouro vira
   GAP com `[CEILING-FORCED]` (distingue truncado de inconclusivo).
6. **Medir antes/depois**: `scripts/cost-snapshot.sh` congela baseline (evals/tokens/);
   A/B com N≥10 sessões nas 12 queries do golden-set exigindo delta ≥0 em estabilidade
   de rota e veracidade (`verified_bad` conta). Economia sem gate de qualidade é inválida.
