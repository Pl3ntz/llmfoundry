# Security + Dev Team Agents & PDF Tooling — SPEC

**Status:** Aprovado para implementação
**Autor:** vplentz
**Data:** 2026-08-02
**Complexidade:** Complexo
**Tipo:** Feature (agentes + MCP) no LLMFoundry
**Entrega:** via branch `feat/security-agents` + worktree + PR documentada

---

## O que

1. Criar **3 agentes de segurança** (red-team, blue-team, bug-bounty-hunter) que roteiam
   para as 145 skills de security já instaladas no opencode.
2. Adicionar **pdf-inspector** (MIT, gratuito) como ferramenta para processar PDFs
   localmente, rápido, sem OCR caro.
3. Adicionar **firecrawl-mcp-server** (MIT, gratuito) como MCP opcional para web scraping
   com fontes reais (requer API key do usuário, mas a ferramenta em si é MIT).

## Por que

- O usuário tem 145 skills de security mas **nenhum agente que as orquestre**.
- O repo `uphiago/recon-skills` (1k stars) confirmou: o pacote de skills é o mesmo que o
  usuário já possui. Falta roteamento e disciplina, não conteúdo.
- PDFs (CVs, contratos) são recorrentes no trabalho. pdf-inspector é o melhor da classe
  (0.875 vs 0.735 do pymupdf), 100% local, MIT.
- Tudo gratuito. Nada pago.

## Escopo — Agentes (3)

| Agente | Mode | Papel | Roteia para |
|--------|------|-------|-------------|
| `red-team-agent` | subagent | Ofensivo (autorizado): recon → hunt → exploração | recon-playbook, web2-recon, hunt-*, redteam-mindset |
| `blue-team-agent` | subagent | Defensivo: auditar, corrigir, proteger | security-review, ai-llm-app-security, code-review |
| `bug-bounty-hunter` | subagent | Caça de bug: alvo → recon → validação → report | bb-methodology, hunt-*, triage-validation, report-writing |

Cada agente: `model: opencode-go/deepseek-v4-pro`, `edit: deny`, `bash: ask`,
anti-delirium + human-voice, rotas para skills existentes.

## Escopo — PDF tooling

**pdf-inspector (MIT, gratuito, 5.3k stars):**
- Ferramenta para extrair texto/Markdown de PDFs localmente (<200ms)
- Melhor da classe em benchmark (0.875 overall, 0.47s vs pymupdf 17s)
- Instalação: `pip install pdf-inspector` (Python binding) ou npm
- Adicionar como skill `pdf-processing` no LLMFoundry (instrução de uso) + nota no README

**firecrawl-mcp-server (MIT, gratuito, 7.1k stars):**
- MCP opcional no `opencode.json` (comentado por padrão — requer FIRE_CRAWL_API_KEY)
- Usa a API firecrawl (pode ter custo de uso, mas o servidor MCP é MIT/gratuito)

## Fora de escopo

- NÃO criar novas skills de security (existem 145)
- NÃO duplicar conteúdo do `uphiago/recon-skills`
- NÃO executar testes ofensivos em alvos não autorizados
- NÃO usar nada pago (apiKey paga só se o usuário optar no firecrawl)
- Fase 2: full-stack specialists (frontend/backend/database) — depois desta PR

## Critérios de sucesso

1. 3 agentes criados com frontmatter válido + anti-delirium + human-voice
2. Skill `pdf-processing` criada (usa pdf-inspector)
3. `opencode.json` atualizado (pdf-inspector documentado, firecrawl-mcp comentado)
4. SKILLS.md + README atualizados
5. Routing table do orquestrador atualizada
6. Validação: 45+ frontmatters, 32/32 evals, CI green
7. **Entrega: worktree + branch + commits atômicos + PR documentada**

## Plano de execução

1. Criar `agents/red-team-agent.md`, `blue-team-agent.md`, `bug-bounty-hunter.md`
2. Criar `skills/pdf-processing/SKILL.md`
3. Atualizar routing table no `ai-orchestrator.md`
4. Atualizar `opencode.json` (pdf-inspector nota, firecrawl comentado)
5. Atualizar SKILLS.md + README
6. Validar (frontmatters, evals, human-voice)
7. Commits atômicos na branch `feat/security-agents`
8. Abrir PR documentada
