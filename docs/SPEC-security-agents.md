# Security Agents — SPEC

**Status:** Draft para revisão
**Autor:** vplentz
**Data:** 2026-08-02
**Complexidade:** Médio
**Tipo:** Feature (agentes no LLMFoundry)

---

## O que

Criar 3 agentes de segurança no LLMFoundry que **roteiam para as 145 skills de security
já instaladas** no opencode (recon, hunt-*, bb-methodology, triage, report). Os agentes
orquestram, as skills executam. Não criar skills novas (já existem).

## Por que

O usuário tem 145 skills de security/bug bounty no config, mas **nenhum agente dedicado**
que as orquestre. O repo `uphiago/recon-skills` (1k stars) confirmou que o pacote de
skills é o mesmo que o usuário já possui. O valor que falta é **roteamento e disciplina**:
um agente que saiba qual skill usar, em que ordem, com anti-delirium e gates.

## Escopo — 3 agentes

| Agente | Mode | Papel | Roteia para |
|--------|------|-------|-------------|
| `red-team-agent` | subagent | Ofensivo (autorizado): recon → hunt → exploração | recon-playbook, web2-recon, hunt-*, redteam-mindset |
| `blue-team-agent` | subagent | Defensivo: auditar, corrigir, proteger | security-review, ai-llm-app-security, code-review |
| `bug-bounty-hunter` | subagent | Caça de bug: alvo → recon → validação → report | bb-methodology, hunt-*, triage-validation, report-writing |

Cada agente:
- `model: opencode-go/deepseek-v4-pro`
- `permission`: bash=ask, edit=deny (analisam, não modificam)
- Carrega as skills certas conforme o contexto (progressive disclosure)
- Segue anti-delirium (prova ou [UNVERIFIED]) + human-voice

## Fora de escopo

- NÃO criar novas skills de security (existem 145)
- NÃO duplicar o conteúdo do `uphiago/recon-skills`
- NÃO executar testes ofensivos em alvos não autorizados
- NÃO substituir o `ai-orchestrator` (estes são subagents especializados)

## Critérios de sucesso

1. 3 agentes criados em `agents/` com frontmatter válido
2. Cada agente lista as skills que roteia
3. Anti-delirium + human-voice em cada um
4. Registrados no SKILLS.md + README
5. Roteamento no `ai-orchestrator` (routing table)
6. Validação: 42+ frontmatters, 32/32 evals, CI green
7. Entregue via **branch + worktree + PR documentada** (padrão do kit)

## Plano de execução

1. `git worktree add` + branch `feat/security-agents`
2. Criar os 3 agentes (`red-team-agent.md`, `blue-team-agent.md`, `bug-bounty-hunter.md`)
3. Atualizar routing table no `ai-orchestrator`
4. Atualizar SKILLS.md + README
5. Validar (frontmatters, evals, human-voice)
6. Commit atômico + PR documentada
