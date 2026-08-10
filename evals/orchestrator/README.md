# Orchestrator evals

Medem a qualidade do **roteamento do orquestrador** (qual agente/rota para cada tipo
de pedido) e o **uso de gates** (interviewMe, spec, scopeSplit).

## Golden set

`golden-set.json`: 12 perguntas congeladas (não mudar sem razão, bump `version`).
Cada caso tem:

- `prompt`: o pedido do Owner
- `expectedRoute`: rota esperada (deep-researcher, ai-architect, ai-evals-runner,
  llm-security-reviewer, direct, build, interview, ou combinação `+` p/ multi-goal)
- `expectedGates`: gates esperados (`interviewMe`, `spec`, `scopeSplit`)
- `why`: justificativa (para revisar quando o modelo divergir)

## Como rodar

```bash
# bateria completa contra o modelo free (o mesmo que orquestra em produção)
python3 scripts/routing-runner.py --model opencode/deepseek-v4-flash-free

# N amostras por pergunta: mede ESTABILIDADE de rota + taxa de gates
python3 scripts/routing-runner.py --model opencode/deepseek-v4-flash-free --samples 2

# via eval-runner (suite live; NAO faz parte do --suite all, custa modelo)
python3 scripts/eval-runner.py --suite live-routing --samples 2

# só uma pergunta (debug rápido)
python3 scripts/routing-runner.py --question RS-1

# conferir os prompts sem gastar chamada
python3 scripts/routing-runner.py --dry-run
```

O runner usa `opencode run -m opencode/deepseek-v4-flash-free --pure`. O `--pure`
desliga plugins para medir o modelo, não o guard chain. Extrai o JSON de resposta dos
eventos do server e pontua com a mesma régua do `routing-score.py` (rota 0.6,
gates 0.4, pass >= 0.7).

## Critério de falha (importante)

O `live-routing` do `eval-runner.py` falha apenas se a **ROTA for instável**: a rota
escolhida pelo modelo tem de ser a esperada em TODAS as amostras. Isso é a política
determinística. **Gates (interviewMe, spec, scopeSplit) são métrica separada**.
sujeitos a variabilidade do modelo (ex: RS-9 CVE-hunting oscila interviewMe entre
amostras), e não devem falhar o suite sozinhos.

## Estado

| Data | Suite | Perguntas | Passed | % | Modelo | Metric |
|------|-------|-----------|--------|---|--------|--------|
| 2026-08-01 | routing-runner | 6 | 4 | 67% | (anterior) | composite |
| 2026-08-07 | routing-runner | 12 | 12 | 100% | deepseek-v4-flash-free | route-stable |
| 2026-08-07 | live-routing (eval-runner) | 12 | 12 | 100% | deepseek-v4-flash-free | route-stable |
| 2026-08-10 | routing-runner (AB-antes, pré-merge PR #14) | 12 | 12 | 100% | deepseek-v4-flash-free | route-stable |
| 2026-08-10 | routing-runner (pós-merge PR #14) | 12 | 12 | 100% | deepseek-v4-flash-free | route-stable |

Conclusão prática: em bateria fria (sem contexto), o modelo free roteia de forma
estável 12/12. Não há degradação de roteamento em relação ao modelo anterior, nem
após o PR #14 (token economy: AGENTS.md enxuto, skills comprimidos, teto 12+8 do
deep-researcher). Os únicos pontos de atenção são gates de entrevista em perguntas
de segurança (RS-9, RS-12), que variam entre rodadas. Manter `baseline.json` como
registro de regressão e `evals/tokens/ab-antes.json` como ponto de comparação de
tokens do protocolo A/B.