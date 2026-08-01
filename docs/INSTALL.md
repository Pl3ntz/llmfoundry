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

## Chrome DevTools with your logins

The `chrome-devtools` MCP uses `--autoConnect` so it attaches to the Chrome you already
have open (with your sessions/cookies) instead of launching a clean one.

One-time setup:
1. Open your normal Chrome and go to `chrome://inspect/#remote-debugging`
2. Click Enable on the remote debugging prompt
3. That's it. The MCP connects to your authenticated Chrome from then on.

> macOS note: `--userDataDir` does not reliably restore encrypted cookies (Keychain).
> `--autoConnect` to your running Chrome is the reliable way to use your logged-in sessions.

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
