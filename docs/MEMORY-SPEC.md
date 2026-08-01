# LLMFoundry Memory — SPEC v1

**Status:** Rascunho para revisão
**Autor:** vplentz
**Data:** 2026-08-01
**Nome:** LLMFoundry Memory (working name: `foundry-memory`)
**Complexidade:** Complexo

---

## O que

Sistema de memória unificada de aprendizado contínuo para o LLMFoundry. Captura
estruturada de conhecimento das sessões (erros resolvidos, decisões, padrões recorrentes,
achados de agentes), com busca, confiança, reforço e promoção — portando o que o
`local-mind` acerta e corrigindo suas limitações.

## Por que

O usuário tem o `local-mind` (Claude Code) — 1853 memórias, 995 fatos de perfil, 385
gotchas, 205 findings de agentes. A ideia é comprovada. Mas tem limitações que queremos
corrigir na versão LLMFoundry (focada em opencode + DeepSeek + engenharia de IA).

### O que o local-mind acerta (manter)

| Recurso | Detalhe |
|---------|---------|
| FTS5 full-text search | busca lexical com stemming porter |
| Confiança + reforço | fatos ganham peso ao serem re-confirmados |
| Severidade/status em findings | memória acionável, não só texto |
| Container por projeto | isolamento por contexto |
| Recorrência com promoção | gotchas viram regras (3+ ocorrências) |
| Captura por hook | automática, não manual |

### O que o local-mind erra (corrigir)

| Limitação | Correção LLMFoundry |
|-----------|---------------------|
| `recall_log` vazio — captura sem uso medível | Recall com confirmação de ação |
| Só busca lexical, sem correlação semântica | Embeddings (v2) sobre a camada estruturada |
| `session_turn` é tudo — volume de ruído (1848) | **Captura estruturada**: só eventos com sinal |
| Sem expiração/decay | Decay temporal + arquivamento |
| Sem promoção automática medível | Promotion gate com critérios explícitos (matriz do Quarterdeck) |
| Banco proprietário, difícil de versionar/compartilhar | Camada curada em markdown git-versionável |

---

## Decisão de storage (usando nosso setup)

**Nossa realidade:** opencode + DeepSeek (barato, queremos maximizar uso) + kit versionável
no git. Captura estruturada = volume baixo, alto sinal.

**Decisão: SQLite (armazenamento vivo) + Markdown curado (LOCAL, nunca versionado).**

| Camada | Tecnologia | Papel |
|--------|-----------|-------|
| **Viva** | SQLite + FTS5 | Store de eventos estruturados, busca lexical, métricas |
| **Curada** | Markdown em `~/.local/share/llmfoundry/memory/` por projeto | O que sobrevive à sessão — **100% local, nunca no git** |
| **Semântica** | Embeddings (v2, opcional) | Correlação vetorial sobre a camada curada |

> **PRIVACIDADE (regra inviolável):** memória é **local-only, nunca versionada**.
> O repo LLMFoundry (versionado/compartilhado) contém **APENAS templates vazios** com
> placeholders. Nenhuma memória real, regra de negócio, dado pessoal, secret, nome de
> cliente ou snippet proprietário entra no repo. O que for capturado fica em
> `~/.local/share/llmfoundry/memory/` (fora do repo) ou em `.llmfoundry/` gitignored
> por projeto.

**Por que não embeddings na v1:**
1. Captura estruturada = volume baixo → FTS5 lexical resolve a busca.
2. Embeddings adicionam custo de API (embedding models) — contra a filosofia DeepSeek-barato.
3. Vetores não são portáveis/versionáveis; a camada curada local é markdown simples.
4. V2 pode adicionar sqlite-vec sem reescrever nada.

**Privacidade (justificativa):** a memória guarda decisões, gotchas e findings de trabalho
real — conteúdo que NÃO deve sair da máquina nem do repo. Versionar memória = risco de
vazar regra de negócio ou dado pessoal em um repo compartilhado. Por isso a camada curada
é local e o repo carrega só templates sanitizados.

**Por que não só arquivos:**
- O local-mind provou que query estruturada (severidade, status, contagem, confiança) vale.
- SQLite é local, sem servidor, sem infra — igual ao setup.

---

## Escopo — Subsistemas

### 1. Captura (estruturada, hook-driven)

Capturar **eventos com sinal**, não turns:

| Evento | Gatilho | Exemplo |
|--------|---------|---------|
| **Erro resolvido** | `tool.execute.after` (bash falhou → bash ok depois) | "build error X fixed by Y" |
| **Decisão** | `/ai-memory remember` ou detecção no fluxo SPEC | "escolhemos DeepSeek V4 Pro sobre kimi-k3 por custo" |
| **Padrão recorrente** | contagem de gotchas ≥ 3 | "npm install sempre roda como sudo" |
| **Achado de agente** | agentes com findings (deep-researcher, llm-security-reviewer) | "[HIGH] SSRF via fetch tool — fix em X" |
| **Fato estático** | manual | "projeto usa FastAPI + raw SQL, sem ORM" |

Implementação: plugin opencode (`plugins/memory.ts`) nos hooks `tool.execute.after` +
comandos `/ai-memory remember|forget|search|stats`.

### 2. Modelo de dados (SQLite)

```
memories          — eventos estruturados (tipo, conteúdo, container, metadata JSON)
memory_fts        — FTS5 (conteúdo)
memory_facts      — fatos de perfil com confidence + reinforced_count
gotchas           — padrões com hash + count + samples + promoted
findings          — achados de agentes (severity, status, acted_on)
recall_log        — recall com acted_on (corrige o gap do local-mind)
session_metrics   — métricas por sessão
```

### 3. Ciclo de vida da memória

```
CAPTURA (hook/comando)
  → NORMALIZA (dedup por hash, contagem)
  → REFORÇA (confidence++ quando re-observado)
  → DECAY (peso cai com o tempo se não reforçado)
  → PROMOVE (≥3 recorrências + 5 critérios da matriz → MEMORY/*.md LOCAL)
  → ARQUIVA (não usado em 90 dias → movido, não deletado)
```

> Promoção escreve na camada local (`~/.local/share/llmfoundry/memory/<projeto>/`), nunca
> no repo. O repo mantém só `templates/MEMORY/` com exemplos vazios e placeholders.

**Promotion Criteria Matrix** (do Quarterdeck, mantido):
Recorrência ≥3 sessões · Consistência (mesma solução) · Impacto (preveniu erro/ganhou tempo) ·
Estabilidade (sistema não mudou) · Clareza (1-2 frases, ≤200 chars).

### 4. Camada curada (LOCAL, nunca versionada)

Local: `~/.local/share/llmfoundry/memory/<projeto>/`

```
MEMORY/
├── PROJECT.md        # fatos estáticos do projeto
├── DECISIONS.md      # ADRs leves (decisão, por que, quando)
├── GOTCHAS.md        # padrões promovidos com fix
├── FINDINGS.md       # achados abertos/resolvidos
└── INDEX.md          # sumário + estatísticas
```

**Regra de ouro:** esta camada é **100% local**. Se um projeto precisar de memória
versionada, usa-se `.llmfoundry/` no próprio repo **gitignored** — nunca no histórico do
git e nunca no repo compartilhado.

O repo LLMFoundry mantém apenas `templates/MEMORY/` — o mesmo shape com **exemplos vazios
e placeholders**, para o usuário copiar para a camada local. Nenhum conteúdo real.

### 5. Recall com confirmação (corrige o gap)

- Recall acontece quando uma skill/agente consome uma memória.
- `recall_log` registra: o que foi lembrado, quem lembrou, e **acted_on** (foi agido?).
- Se um finding é lembrado 2x sem ação → ele sobe de prioridade ou é marcado stale.

---

## Fora de escopo (v1)

- Embeddings/semantic search (v2)
- Servidor MCP de memória (não precisa, SQLite resolve)
- Captura de turns brutos (rejeitado — ruído)
- Multi-máquina sync (fora de escopo — camada curada é local)

---

## Critérios de sucesso

1. Captura automática de erros resolvidos e achados de agentes (hook)
2. `recall_log` com `acted_on` populado — gap do local-mind corrigido
3. Promoção exige 5 critérios; nada auto-promove sem a matriz
4. Camada curada em markdown **100% local** — repo contém só templates vazios
5. Busca FTS5 + filtros (tipo, severidade, projeto)
6. Zero dependência de servidor; tudo local
7. Consome < 100 requests/API de DeepSeek/mês (não depende de LLM para capturar)

## Critérios de privacidade (invioláveis)

1. **Nenhuma memória real entra no repo.** Repo = só `templates/MEMORY/` com placeholders.
2. **Zero regra de negócio, dado pessoal, secret, nome de cliente** em qualquer artefato versionado.
3. SQLite e markdown curado em `~/.local/share/llmfoundry/` ou `.llmfoundry/` — ambos fora do git.
4. `.gitignore` do LLMFoundry bloqueia `.llmfoundry/`, `memory/`, `*.db` por padrão.
5. O install.sh nunca copia memória; só templates sanitizados.
6. Qualquer conteúdo detectado como PII/secret na captura é descartado ou ofuscado antes de persistir localmente.

---

## Integração com o kit

| Componente | Papel |
|-----------|-------|
| `plugins/memory.ts` | Hooks de captura (tool.execute.after) |
| `commands/ai-memory.md` | `/ai-memory remember|search|forget|stats|promote` |
| `agents/deep-researcher.md` | Findings alimentam `findings` |
| `skills/ai-engineering-standards` | Decisões registradas via `DECISIONS.md` |
| `evals/` | Nada muda; memória não entra no eval |

---

## Plano de implementação (após aprovação da SPEC)

1. `scripts/memory/` — módulo Python/SQLite (schema, insert, search, promote, decay)
2. `plugins/memory.ts` — hooks de captura
3. `commands/ai-memory.md` — CLI surface
4. Camada curada: template `MEMORY/*.md` por projeto
5. Teste: sessão real, verificar recall + promoção
6. Commit + versão
