#!/usr/bin/env bash
# Hook de notificacao da CI do llmfoundry na VPS.
#
# Como usar:
#   1. Copie para ~/llmfoundry-ci/notify.sh e de permissao de execucao:
#        cp notify.example.sh ~/llmfoundry-ci/notify.sh
#        chmod +x ~/llmfoundry-ci/notify.sh
#   2. Preencha um canal abaixo (Telegram, e-mail, webhook).
#   3. O vps-ci.sh chama este script SO quando a CI falha, com:
#        $1 = exit code da CI
#        $2 = caminho do ultimo log
#
# O hook nao pode quebrar a CI: qualquer erro aqui e engolido (|| true).

EXIT_CODE="$1"
LOG_FILE="$2"

# --- Telegram ---------------------------------------------------------------
# Crie um bot com @BotFather, pegue o token e o chat id do seu chat com o bot.
# TELEGRAM_TOKEN="123456:ABC..."
# TELEGRAM_CHAT_ID="123456789"
if [ -n "${TELEGRAM_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
  MSG="llmfoundry CI FALHOU (exit ${EXIT_CODE}). Log: ${LOG_FILE}"
  curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${MSG}" >/dev/null 2>&1
  exit 0
fi

# --- Email (sendmail/mailx) --------------------------------------------------
# MAIL_TO="voce@example.com"
if [ -n "${MAIL_TO:-}" ] && command -v mail >/dev/null 2>&1; then
  { echo "llmfoundry CI FALHOU (exit ${EXIT_CODE})";
    echo "Log: ${LOG_FILE}";
    echo "Ultimas linhas:";
    tail -20 "${LOG_FILE}" 2>/dev/null; } | mail -s "llmfoundry CI FAIL" "${MAIL_TO}"
  exit 0
fi

# --- Webhook generico --------------------------------------------------------
# WEBHOOK_URL="https://hooks.example.com/..."
if [ -n "${WEBHOOK_URL:-}" ]; then
  curl -sS -X POST "${WEBHOOK_URL}" \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"llmfoundry CI FALHOU (exit ${EXIT_CODE})\",\"log\":\"${LOG_FILE}\"}" \
    >/dev/null 2>&1
  exit 0
fi

# Sem canal configurado: apenas registra (a falha ja esta no ci.log de qualquer forma).
echo "[notify] CI FAIL (exit ${EXIT_CODE}), nenhum canal configurado, log: ${LOG_FILE}"
exit 0
