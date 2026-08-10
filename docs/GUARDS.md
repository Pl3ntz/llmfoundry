# Guards Policy

Regras de segurança de plugins do LLMFoundry. Todo plugin novo deve ser classificado
em uma das duas classes. A classificação é a regra de ouro:

> **Um guard que decide roteamento/estilo JAMAIS deve travar produção (fail-open).**
> **Um guard que impede destruição de dados JAMAIS deve avisar em vez de bloquear (fail-close).**

## Classificação atual

| Plugin | Classe | Comportamento | Por quê |
|--------|--------|---------------|---------|
| `gates.ts` | **FAIL-CLOSE** | `throw` em comandos destrutivos (`pkill`, `rm -rf` fora de tmp, `sudo`, etc.) | Segurança de dados/sistema. Erro perigoso não pode passar |
| `delegation-guard.ts` Gate 1 (4 partes obrigatórias) | **FAIL-CLOSE** | `throw` se faltar Objective/Context/Output contract/Boundaries | Erro real de delegação; prompt sem forma gera subagent adivinhando |
| `delegation-guard.ts` Gate 4 (misroute) | **FAIL-OPEN** | `warn` no session, nunca `throw` | Roteamento é decisão do modelo; regex de keyword gerou falsos positivos e loop |
| `delegation-guard.ts` circuit breaker | **FAIL-CLOSE** | `throw` (dead-letter) após N spawns do mesmo alvo na janela | Quebra loop infinito de retry. É o failure mode mais caro |
| `research-guard.ts` | **FAIL-OPEN** | `console.error` aviso (bloqueia só com `LF_RESEARCH_STRICT=1`) | Pesquisa direta do orquestrador é preferência, não erro |
| `publish-guard.ts`, `verify-guard.ts`, `voice-guard.ts`, `chrome-guarantee.ts` | **FAIL-OPEN** | aviso / não destrutivo | Política e conveniência, nunca travam trabalho legítimo |

## Circuit breaker de delegação

QUANDO alguém muda o `delegation-guard.ts`, usar o MISROUTE_RULES e o breaker:

- Parâmetros atuais: `TRIP_WINDOW_MS=60_000`, `MAX_SPAWNS=3`, `COOLDOWN_MS=120_000`.
- Após `MAX_SPAWNS` spawns do mesmo `(session, target)` dentro da janela, o guard `throw`
  (dead-letter) por `COOLDOWN_MS`, avisando para trocar de abordagem em vez de repetir.
- Isolado por `(sessionID, subagent_type)`: um alvo que trip não afeta outro target
  nem outra sessão.
- O breaker roda ANTES do `validateDelegation`. Loop é o failure mais severo.

## Como adicionar um guard

1. Identifique a classe: bloqueia para prevenir dano real (FAIL-CLOSE) ou apenas
   orienta política (FAIL-OPEN)? Marque no comentário de cabeçalho do plugin.
2. Um guard FAIL-OPEN nunca usa `throw`; no máximo `console.error`/advisory no session.
3. Um guard FAIL-CLOSE NUNCA degrada para aviso.
4. Adicione o caso no espelho de teste em `scripts/eval-runner.py` no MESMO commit.
   O espelho duplica a lógica, e o suite `guards` falha se eles divergirem.
5. Rode `python3 scripts/eval-runner.py --suite guards` (20 checks) e depois `--suite all`
   (66 checks) e atualize `evals/baseline.json` se o número de checks mudar.

## Como mudar as regras de RO-teamento

As `MISROUTE_RULES` do delegation-guard agora exigem **combinação de 2 sinais fortes**
(ex: `market`+`competitor` juntos; `malware`+`ghidra` juntos), nunca palavra única.
Isso corta falsos positivos como "binary" (tópico), "baseline" (estado), "recon"
(verbo PT "reconhecer"). Quando mudar o plugin, mude o espelho `_DG_MISROUTE` no
eval-runner.py **no mesmo commit**. A divergência entre plugin e espelho é um bug
de teste, e o suite falha apontando.