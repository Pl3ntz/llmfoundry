#!/usr/bin/env bash
# chrome-check.sh: helper for the chrome-devtools MCP standard.
#
# The chrome-devtools MCP uses --autoConnect to attach to YOUR running Chrome
# (with your logins). This script does NOT open a debug Chrome with user-data-dir
# (that does not restore cookies on macOS). It only:
#   1. Opens your normal Chrome if it is not running
#   2. Checks for orphaned chrome-devtools-mcp processes after aborted runs
#
# Usage:
#   ./scripts/chrome-check.sh open     # open normal Chrome (MCP connects via autoConnect)
#   ./scripts/chrome-check.sh clean    # kill orphaned chrome-devtools-mcp processes
#   ./scripts/chrome-check.sh status   # show Chrome + orphan state

set -euo pipefail

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MODE="${1:-status}"

case "$MODE" in
  open)
    if pgrep -x "Google Chrome" >/dev/null 2>&1; then
      echo "Chrome already running. The MCP (--autoConnect) will attach to it."
    else
      echo "Opening your normal Chrome..."
      open -a "Google Chrome" 2>/dev/null || "$CHROME" &
      echo "Chrome opened. When you use the MCP, approve the debugging prompt."
    fi
    ;;
  clean)
    echo "Killing orphaned chrome-devtools-mcp processes..."
    pkill -f "chrome-devtools-mcp" 2>/dev/null && echo "done" || echo "none found"
    ;;
  status)
    if pgrep -x "Google Chrome" >/dev/null 2>&1; then
      echo "Chrome: running"
    else
      echo "Chrome: not running (MCP autoConnect needs it)"
    fi
    ORPHANS=$(pgrep -fl "chrome-devtools-mcp" | wc -l | tr -d ' ')
    echo "chrome-devtools-mcp orphans: $ORPHANS"
    ;;
  *)
    echo "Usage: $0 {open|clean|status}"
    exit 1
    ;;
esac
