#!/usr/bin/env bash
set -euo pipefail

# LLMFoundry installer — symlinks skills/, agents/, commands/ into ~/.config/opencode.
# Symlinks: edit in the repo, changes reflect in opencode immediately.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${OPENCODE_CONFIG_DIR:-$HOME/.config/opencode}"

if [ ! -d "$CONFIG_DIR" ]; then
  mkdir -p "$CONFIG_DIR"
fi

link() {
  local src="$REPO_DIR/$1"
  local dst="$CONFIG_DIR/$1"
  if [ -L "$dst" ]; then
    rm "$dst"
  elif [ -e "$dst" ]; then
    echo "ERROR: $dst exists and is not a symlink. Move it away first."
    exit 1
  fi
  ln -s "$src" "$dst"
  echo "linked $dst → $src"
}

# Only link directories that exist
for d in skills agents commands plugins; do
  [ -d "$REPO_DIR/$d" ] && link "$d"
done

echo
echo "LLMFoundry installed. Restart opencode to load changes."
echo "Add plugin gates to opencode.json:"
echo '  "plugin": ["/path/to/llmfoundry/plugins/gates.ts"]'
