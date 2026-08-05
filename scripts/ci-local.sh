#!/usr/bin/env bash
# CI local do llmfoundry. Fonte de verdade única: roda o mesmo conjunto de
# verificações determinísticas em qualquer executor (Docker na VPS, Mac, CI).
#
# Uso:  ./scripts/ci-local.sh [diretorio do repo, default: o proprio repo]
# Saida: exit 0 = PASS, exit 1 = FAIL (com o passo que falhou nomeado)
set -uo pipefail

REPO="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO" || { echo "repo nao encontrado: $REPO"; exit 1; }

fail=0
pass()  { printf '  PASS  %s\n' "$*"; }
fails() { printf '  FAIL  %s\n' "$*"; fail=1; }

echo "== llmfoundry CI local =="
echo "repo: $REPO"

# 1. eval-runner: engine, routing golden-set, scorer, plugins, K=5 stability
if python3 scripts/eval-runner.py; then
  pass "eval-runner"
else
  fails "eval-runner"
fi

# 2. frontmatters validos (YAML) em skills, agents e commands
if python3 - <<'EOF'
import glob, sys, yaml
files = glob.glob('skills/*/SKILL.md') + glob.glob('agents/*.md') + glob.glob('commands/*.md')
bad = []
for f in files:
    txt = open(f).read()
    if not txt.startswith('---'):
        bad.append(f'no frontmatter: {f}')
        continue
    try:
        yaml.safe_load(txt.split('---', 2)[1])
    except Exception as e:
        bad.append(f'bad yaml: {f}: {e}')
if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f'frontmatters OK ({len(files)} files)')
EOF
then
  pass "frontmatters"
else
  fails "frontmatters"
fi

# 3. JSONs validos (opencode.json + evals)
if python3 - <<'EOF'
import json, glob, sys
files = ['opencode.json'] + glob.glob('evals/**/*.json', recursive=True)
for f in files:
    try:
        json.load(open(f))
    except Exception as e:
        print(f'bad json: {f}: {e}'); sys.exit(1)
print(f'JSONs OK ({len(files)} files)')
EOF
then
  pass "json"
else
  fails "json"
fi

# 4. voice-check smoke: a disciplina human-voice existe e esta referenciada
if grep -rl "human-voice" skills/ >/dev/null; then
  pass "voice skill present"
else
  fails "voice skill present"
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "Result: CI LOCAL PASS"
  exit 0
fi
echo "Result: CI LOCAL FAIL"
exit 1
