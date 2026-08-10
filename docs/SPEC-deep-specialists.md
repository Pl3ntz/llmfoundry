# Deep Specialists: SPEC

**Status:** ✅ Implementado (2026-08-03). Fleet redesenhado: 14 agentes
**Autor:** vplentz
**Data:** 2026-08-02 (spec), 2026-08-03 (implementação + redesign)
**Complexidade:** Médio
**Tipo:** Feature (agentes de nicho no LLMFoundry)
**Entrega:** branch `feat/fleet-redesign`, plugins em `feat/publish-guard`

---

## O que

Adicionar agentes **especialistas profundos de nicho** (não generalistas) ao LLMFoundry,
alinhados ao trabalho real do usuário e às necessidades do mercado.

## Resultado final (14 agentes)

| Agente | Domínio | Ação |
|--------|---------|------|
| `ai-orchestrator` | Multi-agent coordination | Mantido |
| `ai-architect` | LLM system design | Mantido |
| `ai-evals-runner` | Eval pipeline | Mantido |
| `deep-researcher` | Multi-source research | Mantido |
| `llm-security-reviewer` | LLM app security | Mantido |
| `reverse-engineer` | Binary/firmware analysis | Mantido |
| `bug-bounty-hunter` | Web/API offensive security | Mantido (não merge) |
| `red-team-agent` | Enterprise offensive security | Mantido (não merge) |
| `security-defensive` | Defensive audit/hardening | Renomeado (blue-team-agent) |
| `database-engineer` | Full PostgreSQL stack | **Merge** (db-specialist + sql-perf) |
| `data-model-engineer` | Data modeling | Mantido |
| `backend-architect` | Full backend design | **Novo** (expande api-contract) |
| `api-contract-engineer` | Deep API contract work | Mantido (Tier 2) |
| `platform-engineer` | Infra/DevOps | **Novo** |

## Mudanças do plano original

1. **Security NÃO mergeado**: bug-bounty-hunter e red-team-agent ficam separados (context budget + domínios distintos)
2. **Backend expandido com Tier 2 mantido**: backend-architect cobre 70% das perguntas, api-contract-engineer fica como especialista profundo
3. **Infra adicionado**: platform-engineer cobre o gap de DevOps/infraestrutura
4. **Database mergeado**: um agente único cobre schema + queries (80% dos problemas)

## Fora de escopo

- NÃO generalistas (frontend/backend genéricos)
- NÃO duplicar skills existentes
- NÃO substituir ai-orchestrator
