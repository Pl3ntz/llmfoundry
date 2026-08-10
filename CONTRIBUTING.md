# Contributing to LLMFoundry

Thanks for contributing. The kit follows its own discipline: **SPEC → TDD → worktree →
atomic commit**.

## Workflow

```bash
# 1. Create a worktree for your change
git worktree add ../llmfoundry-feature -b feat/your-change
cd ../llmfoundry-feature

# 2. Write a short SPEC in the PR description (what/why/scope/done)
# 3. Implement with tests (red → green → refactor)
# 4. Verify: check the frontmatter and JSON are valid
# 5. Atomic commit with conventional message
git add <specific files>
git commit -m "feat: ..."
# 6. Open a PR
```

## Adding a skill

1. Create `skills/<name>/SKILL.md`
2. Frontmatter: `name` (lowercase-kebab, matches folder) + `description` (what + when to use)
3. Body: workflow the agent follows, steps, verification gate, anti-rationalization
4. Keep `SKILL.md` < 500 lines; put long references in `references/`
5. Add it to `SKILLS.md`

## Adding an agent

1. Create `agents/<name>.md`
2. Frontmatter: `description`, `mode: subagent`, `model: opencode/deepseek-v4-flash-free`, `permission`
3. Include: operating rules, output contract, memory loop (feed the memory)
4. Register in `SKILLS.md`

## Adding a command

1. Create `commands/<name>.md`
2. Frontmatter: `description`, `model: opencode/deepseek-v4-flash-free`, optional `agent`
3. Add to README commands list

## Adding an eval

1. Add `evals/<name>/golden-set.json` (frozen questions with expected behavior + traps)
2. Add `evals/<name>/rubric.json` (dimensions + scoring method)
3. For routing evals, use `scripts/routing-score.py`

## Validation before submitting

```bash
# frontmatter YAML parses
python3 -c "import yaml,glob;[yaml.safe_load(open(f).read().split('---',2)[1]) for f in glob.glob('skills/*/SKILL.md')+glob.glob('agents/*.md')+glob.glob('commands/*.md')]"

# JSON valid
python3 -c "import json,glob;[json.load(open(f)) for f in glob.glob('evals/**/*.json',recursive=True)]"
```

## Rules

- Model IDs are always `opencode/deepseek-v4-flash-free` (never `opencode-go/*`,
  never paid/expensive models — the free-only policy).
- No secrets, PII, or business rules in any versioned file, memory is local-only.
- Conventional commits: `feat:|fix:|refactor:|docs:|test:|chore:|perf:|ci:`.

### Structure sync (MANDATORY on every PR)

**Any change to the project structure must keep everything in sync.** When you add, remove,
or change agents, skills, commands, plugins, or MCPs, the PR must update ALL of:

1. **`SKILLS.md`**: the catalog (agents, skills, commands)
2. **`README.md`**: counts (agents/skills), the team diagram, the agents table, the
   skill catalog
3. **`agents/ai-orchestrator.md`**: the routing table (so the orchestrator routes to the
   new piece)
4. **`skills/ai-orchestration/SKILL.md`**: the routing table (the skill the orchestrator
   loads)
5. **`docs/`**: any doc that names the structure (architecture, model policy)

**Why:** the orchestrator can only route to what it knows. A new agent the routing table
does not mention is invisible. The PR description must state what was synced, and the CI
must pass before merge. A structural change that does not update the routing tables is an
incomplete PR.
