#!/usr/bin/env bash
# CI do llmfoundry rodando na VPS, sem GitHub Actions.
# Cron chama este script. Ele sincroniza o repo e roda a imagem Docker.
#
# Cron sugerido (diario as 06:00):
#   0 6 * * * /home/USER/llmfoundry-ci/run-ci.sh
set -euo pipefail

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

WORK_DIR="${HOME}/llmfoundry-ci"
REPO_DIR="${WORK_DIR}/repo"
IMAGE="llmfoundry-ci:latest"
LOG_DIR="${WORK_DIR}/logs"
TS="$(date +%Y-%m-%d_%H%M%S)"

mkdir -p "${LOG_DIR}"

if [ ! -d "${REPO_DIR}/.git" ]; then
  git clone --quiet https://github.com/Pl3ntz/llmfoundry.git "${REPO_DIR}"
else
  git -C "${REPO_DIR}" fetch --quiet origin main
  git -C "${REPO_DIR}" reset --hard --quiet origin/main
fi

docker run --rm -v "${REPO_DIR}":/workspace:ro "${IMAGE}" \
  > "${LOG_DIR}/ci_${TS}.log" 2>&1
code=$?

echo "[$(date '+%Y-%m-%d %H:%M')] CI $([ "$code" -eq 0 ] && echo PASS || echo "FAIL (exit $code)")" \
  >> "${WORK_DIR}/ci.log"

# mantem os ultimos 30 logs
ls -t "${LOG_DIR}"/ci_*.log 2>/dev/null | tail -n +31 | xargs -r rm -f

exit "$code"
