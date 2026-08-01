#!/usr/bin/env bash
set -euo pipefail

# LLMFoundry installer
#
# Strategy (safe coexistence with existing skills):
# - skills/   → registered via `skills.paths` in opencode.json (does NOT touch the
#               existing ~/.config/opencode/skills/ directory with security skills)
# - agents/   → per-file symlinks (no name collisions expected)
# - commands/ → per-file symlinks
# - plugins/  → registered in opencode.json plugin array
#
# Symlinks: edit in the repo, changes reflect in opencode immediately.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${OPENCODE_CONFIG_DIR:-$HOME/.config/opencode}"
CONFIG_FILE="$CONFIG_DIR/opencode.json"

echo "=== LLMFoundry install ==="

# 0. Python deps (memory engine + optional semantic search). Never fails the install.
echo "[deps]"
if command -v python3 >/dev/null 2>&1; then
  python3 -m pip install -q -r "$REPO_DIR/requirements.txt" 2>/dev/null \
    && echo "  python deps OK (fastembed/numpy for semantic memory)" \
    || echo "  python deps skipped (memory will run lexical-only)"
else
  echo "  python3 not found (memory engine requires it)"
fi

# 1. Link agents (per-file, preserve existing)
echo "[agents]"
mkdir -p "$CONFIG_DIR/agents"
for f in "$REPO_DIR"/agents/*.md; do
  [ -f "$f" ] || continue
  ln -sfn "$f" "$CONFIG_DIR/agents/$(basename "$f")"
  echo "  linked agents/$(basename "$f")"
done

# 2. Link commands (per-file, preserve existing)
echo "[commands]"
mkdir -p "$CONFIG_DIR/commands"
for f in "$REPO_DIR"/commands/*.md; do
  [ -f "$f" ] || continue
  ln -sfn "$f" "$CONFIG_DIR/commands/$(basename "$f")"
  echo "  linked commands/$(basename "$f")"
done

# 3. Register skills.paths + gates plugin in opencode.json (via python for safe JSON editing)
echo "[config]"
python3 - "$CONFIG_FILE" "$REPO_DIR" <<'PY'
import json, sys, os

config_path, repo_dir = sys.argv[1], sys.argv[2]
with open(config_path) as f:
    cfg = json.load(f)

skills_path = os.path.join(repo_dir, "skills")
skills = cfg.setdefault("skills", {})
paths = skills.setdefault("paths", [])
if skills_path not in paths:
    paths.append(skills_path)
    print(f"  added skills.paths: {skills_path}")
else:
    print(f"  skills.paths already present: {skills_path}")

for plugin_name in ("gates.ts", "memory.ts"):
    plugin_path = os.path.join(repo_dir, "plugins", plugin_name)
    plugins = cfg.setdefault("plugin", [])
    if plugin_path not in plugins:
        plugins.append(plugin_path)
        print(f"  added plugin: {plugin_path}")
    else:
        print(f"  plugin already present: {plugin_path}")

with open(config_path, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
    f.write("\n")
PY

echo
echo "LLMFoundry installed. Restart opencode to load changes."
