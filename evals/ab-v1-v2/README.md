# A/B: deep-researcher (v1) vs deep-researcher-v2

Teste comparativo rigoroso rodado em 2026-08-05: os dois agents pesquisaram o
mesmo golden set (3 perguntas com fatos verificados ao vivo em fontes
primárias), 3 runs cada = 18 execuções pelo caminho real de delegação
(ai-orchestrator → task → subagent).

## Golden set (fatos verificados em 2026-08-05)

| Q | Pergunta | Fatos-ouro |
|---|----------|-----------|
| Q1 | Data de lançamento da Python 3.12.0 + principal novidade | 3.12.0, 2023, PEP 701, PEP 695, f-string |
| Q2 | Versão LTS atual do Node.js em 2026 + quando lançada | v24, Krypton, v22, Jod, 2025 |
| Q3 | Data do PostgreSQL 16 + principal melhoria | PostgreSQL 16, 2023, parallel(ization) |

Fatos verificados: python.org (2 out 2023, PEP 701), nodejs.org (v24 Krypton
mai 2025, v22 Jod), postgresql.org (14 set 2023, query parallelism).

## Resultado (recall sobre golden, 9 runs/agent)

| Métrica | v1 | v2 |
|---------|-----|-----|
| Recall médio | 85.6% | 80.7% |
| URLs citadas vivas | 26/26 | 29/29 (2 falhas = falso-negativo do verificador) |
| Claims VERIFIED com fonte | 0 (mecanismo não existe) | 7 |
| Custo médio por run | ~US$0.003 | ~US$0.008 |
| Latência média | ~90s | ~130s |

## Veredito (qualitativo)

- **v2 é mais verificável**: cada claim VERIFIED carrega trecho verbatim
  confirmado na URL (ex: nodejs.org "v24.19.0 Latest LTS"). v1 afirma com
  lista de fontes, sem prova de leitura.
- **v1 é mais abrangente e barato**: menciona dados periféricos (v22/Jod no Q2)
  que o v2 às vezes omite ao focar no essencial da pergunta; ~2.5x mais barato
  e ~1.4x mais rápido.
- **Fabricação: nenhum dos dois fabricou URLs** (100% vivas nos dois).

Decisão depende do caso de uso: verificabilidade/auditoria → v2; cobertura e
custo → v1.

## Re-rodar

```bash
# rodar batch completo (API spend, ~20 min): 
python3 scripts/ab-compare-research.py --runs 3
# re-pontuar evidência salva sem gasto de API:
python3 scripts/ab-score.py
```

Evidência crua em `raw/` (Q1-Q3, run1-3, um JSON por execução).
