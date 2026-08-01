# Install Guide

Install LLMFoundry into opencode. Works alongside existing opencode config.

## Requirements

- [opencode](https://opencode.ai) (v1.16+)
- python3 (for the memory engine)
- DeepSeek V4 access: Go plan (`opencode-go/*`) or API key

## Install

```bash
git clone git@github.com:Pl3ntz/llmfoundry.git
cd llmfoundry
./scripts/install.sh
```

What it does:
1. **agents/** → per-file symlinks into `~/.config/opencode/agents/`
2. **commands/** → per-file symlinks into `~/.config/opencode/commands/`
3. **skills/** → registered via `skills.paths` in `opencode.json` (does NOT touch
   existing security skills)
4. **plugins/** → gates.ts + memory.ts registered in `opencode.json`
5. **Python deps** → `pip install -r requirements.txt` (fastembed/numpy for semantic
   memory). Never fails the install, memory runs lexical-only without it.

Restart opencode. `ai-orchestrator` becomes the default agent.

## Verify

```bash
# agents present
ls ~/.config/opencode/agents/
# should include ai-orchestrator.md, deep-researcher.md, etc.

# opencode.json has the plugins and skills.paths
cat ~/.config/opencode/opencode.json
```

## Chrome DevTools with your logins (THE standard)

The `chrome-devtools` MCP connects to **your running Chrome** (with your sessions and
cookies) using `--autoConnect`. It never launches a clean Chrome. This is the only mode
we use.

Config (both global and repo):
```json
"chrome-devtools": {
  "command": ["npx", "-y", "chrome-devtools-mcp@latest", "--autoConnect", "--channel", "stable"]
}
```

### The allow flow (how it works)

1. The user asks for a browser action (navigate, screenshot, inspect).
2. The MCP connects to the user's Chrome, which shows a debugging-permission prompt.
3. The user approves it. The MCP then works with the user's logged-in session.
4. Done. The user drives the MCP; the approval is part of the flow.

### Rules (non-negotiable)

- **Never** use `--userDataDir` (does not restore encrypted cookies on macOS).
- **Never** force-connect or auto-run tests that bypass the allow prompt.
- **Never** run batch test runners that spawn many opencode sessions touching the MCP
  (they leave orphaned chrome-devtools-mcp processes that fall back to a clean Chrome).
  After any aborted run, check: `pgrep -fl chrome-devtools-mcp` and kill orphans.
- The user is the one who triggers the MCP and approves it. We do not drive it ourselves.

## Memory location

Data (never versioned):
```
~/.local/share/llmfoundry/memory/memory.db
~/.local/share/llmfoundry/memory/vectors.npz
```

## Uninstall

```bash
# remove symlinks
rm ~/.config/opencode/agents/ai-*.md ~/.config/opencode/commands/ai-*.md
# remove plugins from opencode.json plugin array
# remove skills.paths entry
# optionally remove memory data
rm -rf ~/.local/share/llmfoundry/memory
```
