# Deep Specialists — SPEC

**Status:** Draft para revisão
**Autor:** vplentz
**Data:** 2026-08-02
**Complexidade:** Médio
**Tipo:** Feature (agentes de nicho no LLMFoundry)
**Entrega:** via branch + worktree + PR documentada (padrão do kit)

---

## O que

Adicionar agentes **especialistas profundos de nicho** (não generalistas) ao LLMFoundry,
alinhados ao trabalho real do usuário: banco de dados, NL→SQL, performance de query,
multi-tenant, e infraestrutura de produção.

## Por que

O usuário trabalha com sistemas de dados reais (PostgreSQL 44M rows, NL→SQL, RLS,
outbox, multi-tenant no gestor-ai). Generalistas (frontend/backend) são o que qualquer
modelo já faz. O valor está em especialistas que conhecem a profundidade do domínio.

## Escopo — 4 especialistas profundos

| Agente | Modo | Profundidade (não generalista) |
|--------|------|--------------------------------|
| `database-specialist` | subagent | PostgreSQL profundo: schema design, índices, planos (EXPLAIN), RLS, migrations, outbox, tuning, custo de query |
| `sql-performance-engineer` | subagent | Planos de execução, EXPLAIN ANALYZE, índices, N+1, custo de query, otimização multi-tenant |
| `api-contract-engineer` | subagent | FastAPI/Hono profundo: contract-first, auth, idempotência, streaming, error semantics |
| `data-model-engineer` | subagent | Modelagem de dados: normalização, particionamento, chaves, tenancy, evolução de schema |

## Fora de escopo

- NÃO generalistas (frontend/backend genéricos)
- NÃO duplicar skills existentes
- NÃO substituir ai-orchestrator

## Critérios de sucesso

1. 4 agentes criados com frontmatter válido
2. Cada um com profundidade real de domínio (não genérico)
3. Anti-delirium + human-voice
4. Routing table atualizada
5. 50+ frontmatters, 32/32 evals, CI green
6. Worktree + branch + commits atômicos + PR documentada

## Plano

1. `git worktree add` + branch `feat/deep-specialists`
2. Criar os 4 agentes
3. Atualizar routing + SKILLS.md + README
4. Validar + commits atômicos + PR
