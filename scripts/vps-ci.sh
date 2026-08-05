#!/usr/bin/env bash
# CI do llmfoundry rodando na VPS, sem GitHub Actions.
# Cron chama este script. Ele sincroniza o repo, rebuilda a imagem se o
# Dockerfile mudou, roda a CI e notifica em caso de falha.
#
# Cron sugerido (diario as 06:00):
#   0 6 * * * /home/USER/llmfoundry-ci/run-ci.sh
#
# Notificacao: se existir ~/llmfoundry-ci/notify.sh (executavel), ele e chamado
# com o exit code e o caminho do log quando a CI falha. Veja notify.example.sh.
set -euo pipefail

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

WORK_DIR="${HOME}/llmfoundry-ci"
REPO_DIR="${WORK_DIR}/repo"
IMAGE="llmfoundry-ci:latest"
LOG_DIR="${WORK_DIR}/logs"
TS="$(date +%Y-%m-%d_%H%M%S)"
DOCKERFILE_LOCAL="${WORK_DIR}/Dockerfile"
DOCKERFILE_REPO="${REPO_DIR}/ci/Dockerfile"

mkdir -p "${LOG_DIR}"

if [ ! -d "${REPO_DIR}/.git" ]; then
  git clone --quiet https://github.com/Pl3ntz/llmfoundry.git "${REPO_DIR}"
else
  git -C "${REPO_DIR}" fetch --quiet origin main
  git -C "${REPO_DIR}" reset --hard --quiet origin/main
fi

# Rebuild automatico: se o Dockerfile do repo mudou, rebuilda a imagem antes
# do run. Compara checksum, nao data, entao um pull que nao muda nada nao
# dispara build.
if [ -f "${DOCKERFILE_REPO}" ]; then
  if [ ! -f "${DOCKERFILE_LOCAL}" ] \
     || ! cmp -s "${DOCKERFILE_LOCAL}" "${DOCKERFILE_REPO}"; then
    echo "[$(date '+%Y-%m-%d %H:%M')] Dockerfile mudou, rebuildando imagem..."
    cp "${DOCKERFILE_REPO}" "${DOCKERFILE_LOCAL}"
    docker build -t "${IMAGE}" -f "${DOCKERFILE_LOCAL}" "${WORK_DIR}" \
      >> "${WORK_DIR}/build.log" 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M')] build exit=$?" >> "${WORK_DIR}/build.log"
  fi
fi

docker run --rm -v "${REPO_DIR}":/workspace:ro "${IMAGE}" \
  > "${LOG_DIR}/ci_${TS}.log" 2>&1
code=$?

echo "[$(date '+%Y-%m-%d %H:%M')] CI $([ "$code" -eq 0 ] && echo PASS || echo "FAIL (exit $code)")" \
  >> "${WORK_DIR}/ci.log"

# notifica em falha se o hook existir
if [ "$code" -ne 0 ] && [ -x "${WORK_DIR}/notify.sh" ]; then
  "${WORK_DIR}/notify.sh" "$code" "${LOG_DIR}/ci_${TS}.log" || true
fi

# mantem os ultimos 30 logs
ls -t "${LOG_DIR}"/ci_*.log 2>/dev/null | tail -n +31 | xargs -r rm -f

exit "$code"
