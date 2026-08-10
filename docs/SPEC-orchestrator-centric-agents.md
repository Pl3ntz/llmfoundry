# SPEC — Estrutura Orquestrador-Cêntrica (subagents 100% para o orquestrador)

> Status: **RASCUNHO PARA APROVAÇÃO v0.2** — atualizado 2026-08-10.
> Dono: vitor. Nenhum arquivo de agent foi alterado ainda. Este doc é o ponto de partida
> da mudança estrutural. Abrir sessão no llmfoundry e tocar daqui.

## Objetivo central (amarração)

Toda mudança neste repo serve a um objetivo: **conseguir projetos que paguem em dólar,
com qualidade de AI engineering que se vende sozinha**. Esta SPEC é um meio, não um fim:
agentes orquestrador-cêntricos = saída uniforme e mensurável = entregas que impressionam
cliente/recrutador = menos retrabalho por ambiguidade. Nada aqui pode virar "engenharia
pela engenharia" — se um passo não reduz custo ou aumenta qualidade percebida, ele sai do
escopo.

## Contexto (o que decidimos)

Hoje cada subagent produz um output contract estruturado, mas ainda com sobras de prosa
"legível por humano" (formato de relatório). O Owner já **não lê agents há muito tempo**:
ele lê a síntese do orquestrador (≤300 tokens, fan-in do `ai-orchestration/SKILL.md:96`).
A decisão desta sessão foi levar isso até o fim de forma consciente:

**Os subagents passam a ser instrumentos 100% voltados para o orquestrador, não para o
Owner. A tradução para linguagem humana acontece em UM único ponto: o orquestrador.**

Motivos aprovados: economia de tokens, estrutura/organização e mensurabilidade de
performance por agent (evals).

## O que muda (visão geral)

| De (hoje) | Para (orquestrador-cêntrico) |
|---|---|
| Output contract estruturado + sobras narrativas | Pacote estrito: claim + evidência + contradição + DECISION IMPACT |
| Agents escrevem como se o Owner fosse ler | Agents escrevem para o orquestrador arbitrar |
| Tradução humana espalhada | Tradução exclusiva do orquestrador |
| Qualidade julgada por leitura | Qualidade medida por evals (score de aderência ao contrato) |
| Prosa em caixinhas | Schema validável por papel → guard valida automaticamente |

## Por que mensurabilidade é o argumento mais forte

Economia de tokens é real mas modesta (outputs já são curtos, ex.: deep-researcher <800
tokens de corpo). O ganho grande é: estrutura rígida = saída parseável = avaliável.
Isso habilita check automático por agent: a FINDING tem fonte? a contradição foi
reportada? o DECISION IMPACT bate com as evidências? Resultado: sair de "achei que
ficou bom" para "score de aderência ao contrato, por agent, por missão".

## A peça de engenharia obrigatória

"Estruturado" só é mensurável se for **validável**, não só bonito. Prosa em caixinhas
continua sendo prosa. Elementos necessários:

1. **Schema de output por papel de agent**: campos obrigatórios, tipos, presença de
   evidência (`file:line`, URL, excerpt), contradições, DECISION IMPACT.
2. **Validadores por papel** (script determinístico): verificar o contrato
   automaticamente. O `verify-guard.ts` hoje só faz hedge-scan e já pula blocos
   `### FINDINGS` (`plugins/verify-guard.ts:48`) — ele sabe que existe formato
   estruturado mas não valida os campos. Estender para validar headers obrigatórios.
3. **Evals por agent**: para cada papel, definir o que medir em cada missão.

### Formato do contrato: decisão

**Markdown estruturado, não JSON puro.** Motivo: modelo free (DeepSeek V4) tem
guardrails baixos; JSON estrito em todo output gera mais parse-falhas que valor.
Markdown com headers fixos já é robusto (deep-researcher entrega os 8 `###` hoje,
`agents/deep-researcher.md:199`). O validador parseia headers + regex de evidência.
JSON Schema fica reservado para casos onde parse é crítica (ex.: findings para
ferramentas externas), decidido por papel, não por padrão.

### Esquema de validação por papel (v0.3 — após debate com agents)

**Regra transversal (v0.3, ajuste do debate)**: `DECISION IMPACT` é **condicionado**.
O critério de decisão NÃO nasce no subagent — o orquestrador declara a decisão no
`## Context` do spawn (ex.: "o Owner decide entre X e Y; sua pesquisa decide qual é
mais barato"). O agent só preenche DECISION IMPACT se o critério foi fornecido. Se o
orquestrador não sabe qual decisão a missão serve, a missão não deveria ter sido
lançada (resultado sem impacto de decisão = GAP de desenho de missão, ai-architect).

**Validação por resolução de referência, não presença** (ai-architect + ai-evals-runner):
- cada claim cruza com FINDINGS e SOURCES (`[n]` resolve em SOURCES)
- DECISION IMPACT deve referenciar uma linha de FINDINGS (mesmo padrão `[n]`)
- aderência ao contrato é condição necessária, não suficiente: nenhum promote com
  score estrutural sozinho; veracidade (`verified_bad`) manda (ai-evals-runner)

**deep-researcher** (contrato atual em `agents/deep-researcher.md:172-201`):
- [ ] Obrigatório: `### FINDINGS`, `### GAPS`, `### NEXT STEP`, `### SOURCES`
- [ ] Cada FINDING começa com `[VERIFIED|HIGH|MEDIUM|LOW|UNVERIFIED]`
- [ ] Pelo menos 1 SOURCE indexada por FINDING (referência `[n]` resolve em SOURCES)
- [ ] Corpo <800 tokens excluindo SOURCES
- [ ] `### DECISION IMPACT` somente se o critério de decisão foi fornecido no Context
- [ ] `### AUDIT TRAIL` redundante com SOURCES em 90% (deep-researcher) → manter SOURCES
      como âncora; AUDIT TRAIL só para cadeia de proveniência sob demanda (query que
      levou a cada fonte), ativado por comando explícito do orquestrador

**ai-architect** (contrato atual em `agents/ai-architect.md:67-85`):
- [ ] Obrigatório: `### DECISION SUMMARY`, `### ARCHITECTURE`, `### TRADE-OFFS`,
      `### FAILURE MODES`, `### EVAL PLAN`
- [ ] TRADE-OFFS com ≥2 opções comparadas (tabela ou lista)
- [ ] `### DECISION IMPACT` somente se o critério de decisão foi fornecido no Context
- [ ] `### AUDIT TRAIL` para decisões de design com justificativa (aqui sim, distinto)

**orquestrador** (fan-in): continua no formato `ai-orchestration/SKILL.md:78-93`,
sem mudança estrutural — ele já é o único tradutor.

## Evals por agent (o que medir)

| Papel | Métrica | Passa quando |
|---|---|---|
| deep-researcher | Aderência ao contrato | 8 headers presentes, toda FINDING com fonte indexada, DECISION IMPACT condicionado, <800 tokens |
| deep-researcher | Veracidade | Amostra de claims VERIFIED: citação verbatim confere (`verified_bad` conta) |
| ai-architect | Aderência ao contrato | 5 headers + DECISION IMPACT condicionado + AUDIT TRAIL, TRADE-OFFS ≥2 opções |
| orquestrador | Estabilidade de rota | Golden-set 12/12 (já existe: `evals/orchestrator/golden-set.json`, `scripts/routing-runner.py`) |

Implementação: extender `scripts/eval-runner.py` ou novo `scripts/contract-score.py` que
parseia o output de uma missão e devolve score de aderência + veracidade. Roda como eval
por agent, não como guard de bloco (guard pega no vôo, eval mede no tempo). Nenhum
promote com base em score estrutural sozinho.

## Onde a economia de tokens realmente aparece

1. **Contexto do orquestrador**: sem reparse de narrativa; arbitrar direto sobre campos →
   menos compactação, menos perda.
2. **Reuso entre sessões**: ledger persistente evita re-pesquisar o que já foi fechado
   (a maior economia real, via memória, não via formato).
3. **Detecção precoce de lixo**: agent fora do contrato é pego pelo guard antes de
   custar iteração na frente do Owner.

## Riscos aceitos e mitigação

| Risco | Mitigação |
|---|---|
| Bottleneck no orquestrador (toda qualidade final passa por ele) | Evals por agent medem a máquina; ainda assim é risco assumido |
| Distância entre Owner e trabalho bruto | Manter **árvore de evidência acessível sob demanda**: qualquer conclusão vem com "abrir evidência" (fontes, `file:line`, excerpts) |
| Confiança cega ("lixo bonito embalado") | Evals + obrigação de citar evidência na síntese (anti-delirium) |
| Schema vira burocracia (agent gasta tokens preenchendo campos vazios) | Validador marca campos vazios como "n/a aceito" por papel; evals medem conteúdo, não presença cega |

## Plano de execução (ordem importa)

**NÃO tocar nos 14 agents antes de congelar o contrato** (retrabalho garantido).

1. **SPEC da mudança estrutural** (este doc, agora em rascunho v0.2):
   - [x] Template único de output packet: claim + evidência + contradição + DECISION IMPACT + âncora de auditoria
   - [x] Schema validável por papel de agent (2 pilotos definidos)
   - [x] Evals por agent (o que medir em cada papel)
   - [x] O que NÃO muda: árvore de evidência sob demanda, fan-in do orquestrador
2. **Prova de conceito** em 2 agents piloto (deep-researcher + ai-architect):
   antes/depois, apresentar ao Owner.
3. **Rolar para os outros 12 agents** com aprovação.
4. Atualizar skills que dependem dos formatos: `ai-orchestration`, `ai-engineering-standards`,
   `anti-delirium`, e plugins `delegation-guard`, `verify-guard`, `research-guard`.

## Entregável do output packet (template final proposto)

```
### FINDINGS
- [VERIFIED|HIGH|MEDIUM|LOW|UNVERIFIED] [claim] ([N fontes independentes]) [evidência]

### CONTRADICTIONS
- [A diz X] vs [B diz Y]: [qual é mais forte e por quê]

### DECISION IMPACT          <- NOVO: o valor central
- [2-3 linhas: o que isso muda na decisão do Owner + roteamento sugerido ao orquestrador]

### AUDIT TRAIL              <- permanente, para auditoria sob demanda
- [fonte, file:line, URL, excerpt]

### GAPS / NEXT STEP
```

## Pendências de backlog (deep-researcher)

- [x] ~~`deep-researcher.md:4` usa modelo PAGO~~ — **RESOLVIDO** [VERIFIED, agents/deep-researcher.md:4]
- [x] ~~Sem teto de iterações~~ — **RESOLVIDO (2026-08-10)**: máx. 12 websearch + 8 webfetch,
      estouro vira GAP com tag `[CEILING-FORCED]` (agents/deep-researcher.md ITERATE/CEILING)
- [x] ~~Ledger morre no fim da missão~~ — **RESOLVIDO (2026-08-10)**: LEDGER PERSIST grava resumo
      (pergunta → claims → gaps → fontes) na foundry-memory; missão nova consulta "onde paramos"
- [x] ~~Superfície curta (só websearch + webfetch)~~ — **RESOLVIDO (2026-08-10)**: `curl GET`
      somente-leitura em APIs públicas + chrome-devtools/playwright (OSINT estendido)

## Fato técnico verificado (referência)

O websearch do opencode (v1.18.15) alterna entre **Exa** e **Parallel** por rodízio de
sessão quando nenhum provider é configurado: `OPENCODE_WEBSEARCH_PROVIDER` setado manda;
senão, hash do sessionID (par → exa, ímpar → parallel). `[VERIFIED]` do binário.

## Como abrir sessão a partir daqui

```bash
cd ~/dev/llmfoundry && oc-c   # ou opencode no diretório llmfoundry
```

Referência de memória: foundry-memory ids 851 (decisão estrutural) e 852 (gaps deep-researcher).
