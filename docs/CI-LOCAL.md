# CI local na VPS (sem GitHub Actions)

A CI do llmfoundry roda na VPS pessoal, em container Docker, via cron.
Zero consumo de GitHub Actions. O GitHub Actions virou wrapper opcional e fino
do mesmo script, para portabilidade (ver `.github/workflows/ci.yml`).

## Como funciona

```
cron (06:00) ─→ scripts/vps-ci.sh ─→ git clone/pull do repo
                                   ─→ rebuild automatico da imagem se o Dockerfile mudou
                                   ─→ docker run llmfoundry-ci:latest
                                   ─→ log em ~/llmfoundry-ci/logs/ci_*.log
                                   ─→ histórico em ~/llmfoundry-ci/ci.log
                                   ─→ notify.sh em caso de FAIL (opcional)
```

A fonte de verdade é `scripts/ci-local.sh`, que roda 4 verificações
determinísticas, sem chamada de modelo:

1. `eval-runner.py`: engine, routing golden-set, scorer, plugins TS, K=5 stability, guard regressions
2. Frontmatters YAML válidos em skills, agents e commands
3. JSONs válidos (`opencode.json` + evals)
4. Voice-check smoke (disciplina human-voice referenciada)

Exit 0 = PASS, exit 1 = FAIL. Qualquer falha aparece no log com o passo nomeado.

## Notificação em caso de falha

O `vps-ci.sh` chama `~/llmfoundry-ci/notify.sh` (se existir e for executável)
somente quando a CI falha, passando o exit code e o caminho do log. Há um modelo
em `scripts/notify.example.sh` com Telegram, e-mail e webhook genérico
(preencha as credenciais e renomeie para `notify.sh`).

## Rebuild automático da imagem

O `vps-ci.sh` compara o `ci/Dockerfile` do repo com a cópia local da VPS por
checksum. Se mudou, rebuilda a imagem antes de rodar. Pulls que não alteram o
Dockerfile não disparam build.

## Rodar manualmente (sem cron)

```bash
# na VPS, a qualquer momento:
bash ~/llmfoundry-ci/vps-ci.sh
tail -20 $(ls -t ~/llmfoundry-ci/logs/ci_*.log | head -1)
```

## Instalar em outra máquina

Pré-requisitos: Docker, git.

```bash
mkdir -p ~/llmfoundry-ci
cp scripts/ci-local.sh scripts/vps-ci.sh ci/Dockerfile ~/llmfoundry-ci/
cd ~/llmfoundry-ci && docker build -t llmfoundry-ci:latest -f Dockerfile .

# cron diario as 06:00
(crontab -l 2>/dev/null; echo "0 6 * * * bash $HOME/llmfoundry-ci/vps-ci.sh >> $HOME/llmfoundry-ci/ci.log 2>&1") | crontab -
```

## Rodar no Mac (mesmo script)

```bash
./scripts/ci-local.sh          # precisa de python3, numpy, pyyaml e bun
```

## Notas

- O `vps-ci.sh` clona via HTTPS (repo público, sem chave SSH necessária).
- O cron roda com PATH mínimo; o script exporta um PATH completo no topo.
- Logs são rotacionados: mantém os 30 mais recentes.
- Para mudar a frequência, edite a linha do cron na VPS (`crontab -e`).
