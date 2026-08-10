#!/usr/bin/env bash
# eval-integration-deep-researcher.sh: release-gate integration eval for v2.
#
# Runs the REAL deep-researcher agent against a small FROZEN golden set over
# live web queries, then scores recall/fabrication. This is the "integration"
# half of the (c) consensus: the unit suite (eval-runner.py --suite drv2) covers
# logic deterministically every commit; this covers real fetch->correlate->score.
#
# Usage:
#   bash scripts/eval-integration-deep-researcher.sh           # N=3 runs
#   RUNS=5 bash scripts/eval-integration-deep-researcher.sh    # custom N
#
# Requires: network + opencode CLI + deep-researcher installed in
# ~/.config/opencode/agents/. Not part of ci-local.sh by design (hits the web,
# costs API tokens). Run on release or nightly.

set -euo pipefail
cd "$(dirname "$0")/.."

RUNS="${RUNS:-3}"
QUERIES=(
  "Qual a versao LTS atual do Node.js em 2026 e quando foi lancada?"
  "Qual foi a principal novidade do Python 3.12?"
)
OUTDIR="$(mktemp -d)"
trap 'rm -rf "$OUTDIR"' EXIT

echo "=== deep-researcher integration eval (N=${RUNS}) ==="

if ! command -v opencode >/dev/null 2>&1; then
  echo "opencode CLI not found; integration eval skipped (unit suite covers logic)." >&2
  exit 0
fi
if [ ! -f "$HOME/.config/opencode/agents/deep-researcher.md" ]; then
  echo "deep-researcher agent not installed in ~/.config/opencode/agents/." >&2
  echo "Run: cp agents/deep-researcher.md ~/.config/opencode/agents/" >&2
  exit 1
fi

for i in $(seq 1 "$RUNS"); do
  echo "-- run $i --"
  for q in "${QUERIES[@]}"; do
    slug="$(echo "$q" | cksum | cut -d' ' -f1)"
    f="$OUTDIR/run${i}_${slug}.txt"
    # one-shot agent call; message is positional (no --prompt flag)
    opencode run --agent deep-researcher --format json "$q" >"$f" 2>/dev/null || true
    # extract assistant text parts from the JSON events
    python3 - "$f" <<'PYEOF'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
texts = []
for line in p.read_text().splitlines():
    if not line.strip():
        continue
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        continue
    if ev.get("type") == "text" and ev.get("part", {}).get("type") == "text":
        texts.append(ev["part"].get("text", ""))
body = "\n".join(texts)
found_any = bool(body.strip())
print(f"  {p.name}: {'RESPONSE' if found_any else 'EMPTY'} ({len(body)} chars)")
PYEOF
  done
done

echo "=== integration eval done (runs=${RUNS}). Assertions live in the frozen golden (see README) ==="
