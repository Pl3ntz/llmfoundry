#!/usr/bin/env bash
# chrome-debug.sh — open Chrome with remote-debugging so chrome-devtools MCP
# can connect to YOUR browser (with your logins/cookies) on port 9222.
#
# Usage:
#   ./scripts/chrome-debug.sh            # open Chrome with debugging (or focus if running)
#   ./scripts/chrome-debug.sh --headless # run headless
#
# The chrome-devtools MCP is configured with --browserUrl http://127.0.0.1:9222
# so it connects to THIS Chrome instance instead of launching a clean one.

set -euo pipefail

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT="${CHROME_DEBUG_PORT:-9222}"
PROFILE="${CHROME_DEBUG_PROFILE:-$HOME/Library/Application Support/Google/Chrome/Default}"

if [ ! -x "$CHROME" ]; then
  echo "ERROR: Google Chrome not found at $CHROME"
  exit 1
fi

# Already debugging on the port? Nothing to do.
if curl -s --max-time 2 "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
  echo "Chrome debugging already running on port $PORT. MCP will connect."
  exit 0
fi

echo "Opening Chrome with remote-debugging on port $PORT (using your profile)..."
"$CHROME" \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE" \
  --remote-allow-origins='*' \
  "${@:-}" &
echo "Chrome opened. chrome-devtools MCP connects at http://127.0.0.1:$PORT"
