<!--
  LLMFoundry: AI engineering kit for DeepSeek.
  Keywords for search: AI engineering, LLM agents, RAG, MCP, prompt engineering,
  LLM evals, DeepSeek, opencode, AI agents toolkit, agent skills, quality gates,
  anti-delirium, human voice, orchestrator.
-->
<p align="center">
  <img src="assets/logo.svg" alt="LLMFoundry: AI engineering kit for DeepSeek" width="480">
</p>

<h1 align="center">LLMFoundry</h1>

<p align="center">
  <strong>The AI engineering kit for DeepSeek.</strong><br>
  Build LLM apps, agents, RAG, evals, MCP, with production discipline.
</p>

<p align="center">
  <a href="https://github.com/Pl3ntz/llmfoundry"><img alt="GitHub" src="https://img.shields.io/github/stars/Pl3ntz/llmfoundry?style=social"></a>
  <a href="https://github.com/Pl3ntz/llmfoundry/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-lightgrey.svg"></a>
  <a href="docs/MODEL-POLICY.md"><img alt="Model" src="https://img.shields.io/badge/model-DeepSeek_V4_Pro-2ea44f.svg"></a>
  <a href=".github/workflows/ci.yml"><img alt="CI" src="https://github.com/Pl3ntz/llmfoundry/actions/workflows/ci.yml/badge.svg"></a>
  <a href="evals/baseline.json"><img alt="Tests" src="https://img.shields.io/badge/tests-27%2F27-2ea44f.svg"></a>
  <a href="skills/anti-delirium/"><img alt="Anti-delirium" src="https://img.shields.io/badge/discipline-anti--delirium-2ea44f.svg"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#skill-catalog">Skills</a> ·
  <a href="#agents">Agents</a> ·
  <a href="#commands">Commands</a> ·
  <a href="#plugins">Plugins</a> ·
  <a href="#memory">Memory</a> ·
  <a href="#model-policy">Model</a> ·
  <a href="#documentation">Docs</a> ·
  <a href="#roadmap">Roadmap</a>
</p>

---

**LLMFoundry** is a complete kit to develop production-quality LLM applications on
**DeepSeek** (cheap, high-volume) with engineering discipline. It turns opencode into a
team: an **orchestrator** that understands your intent and delegates to specialist agents,
a **living memory** that learns and feeds itself, and **gates** that block bad output.

> Looking for: AI agents, RAG pipeline, prompt engineering, LLM evals, MCP servers,
> DeepSeek coding, AI engineering best practices, agent skills for opencode? You're in the right place.

## Why LLMFoundry

Four disciplines that make it different:

1. **Cost discipline**, DeepSeek only (V4 Pro/Flash). 35-322x more requests per dollar
   than kimi-k3 on the same plan. Explicit PRO vs FLASH routing.
2. **Mode discipline**, PLAN before BUILD when there's ambiguity or stakes. Never build
   what you don't understand.
3. **Anti-delirium**, every claim has concrete proof (`file:line`, command output, URL)
   or an honest `[UNVERIFIED]` marker. No hallucination, ever.
4. **Human voice**, output never reads like AI-generated text. No dashes, no AI vocabulary,
   no template structure.

---

## Quick Start

```bash
git clone git@github.com:Pl3ntz/llmfoundry.git
cd llmfoundry
./scripts/install.sh
```

The installer:
- symlinks `agents/`, `commands/`, `plugins/` into `~/.config/opencode/`
- registers `skills/` via `skills.paths` (does not touch existing skills)
- installs Python deps for the memory engine (fastembed for semantic search)
- configures all gates + memory + voice + verify plugins

Then restart opencode. The orchestrator becomes your default agent.

> Requires: opencode, python3, DeepSeek V4 (Go plan or API key).
> See [docs/INSTALL.md](docs/INSTALL.md).

---

## The team

```
You ──→ AI Orchestrator (the Captain) ──→ specialist subagents
              │
              ├─ deep-researcher      (deep research with correlation + anti-injection)
              ├─ ai-architect         (LLM system design with trade-offs)
              ├─ ai-evals-runner      (prove it works)
              └─ llm-security-reviewer(security before shipping)
              │
              └─ Living Memory (SQLite + embeddings, self-feeding)
```

The flow: you send a raw idea → the orchestrator **captures intent**, asks one question at
a time until it understands → defines the **SPEC** with you → **rewrites** into a master
prompt → **delegates** with full context → **synthesizes** results and presents options.

---

## Skill Catalog

20 skills in 4 categories. All follow the transversal standards.

### Dev Process (transversal, inherited by all)
| Skill | Use when |
|-------|----------|
| `ai-engineering-standards` | Start of every task, tone, evidence, anti-fabrication |
| `ai-dev-process` | Writing code: SPEC, worktree, TDD, atomic commit |
| `interview-me` | Request is underspecified or high-stakes |
| `ai-orchestration` | Routing, delegation protocol, fan-in synthesis |
| `human-voice` | Write in a natural human voice, never looks AI-generated |
| `anti-delirium` | Prove it or don't say it, evidence or confidence marker on every claim |
| `git-workflow` | Committing, branching, merging, resolving conflicts |
| `pull-request` | Creating and updating effective PRs |
| `code-review` | Extremely effective review, five-axis method, before merge |

### AI Core
| Skill | Use when |
|-------|----------|
| `ai-prompt-engineering` | Writing/iterating prompts |
| `ai-agent-patterns` | Designing agentic systems |
| `ai-context-engineering` | Managing context windows |
| `ai-rag-pipeline` | Building retrieval systems |
| `ai-evals` | Proving behavior, guarding regressions |
| `ai-model-integration` | Wiring providers, streaming, fallback |
| `ai-mcp-development` | Building MCP servers |
| `ai-agent-safety` | Sandboxing, permissions, fail-closed |
| `ai-llm-app-security` | Defensive LLM security (OWASP LLM Top 10) |
| `ai-llm-observability` | Tracing, cost/token tracking |

### AI Advanced
| Skill | Use when |
|-------|----------|
| `ai-research` | Deep research with correlation |
| `doubt-driven-development` | High-stakes review: CLAIM/EXTRACT/DOUBT/RECONCILE |
| `source-driven-development` | Grounding decisions in official docs |
| `debugging-and-error-recovery` | 5-step debugging |

Full catalog: [SKILLS.md](SKILLS.md)

---

## Agents

| Agent | Mode | Role |
|-------|------|------|
| [ai-orchestrator](agents/ai-orchestrator.md) | primary (default) | The Captain, interprets, discusses, delegates, synthesizes |
| [deep-researcher](agents/deep-researcher.md) | subagent | Deep research with correlation + anti-injection |
| [ai-architect](agents/ai-architect.md) | subagent | LLM system architecture with trade-offs |
| [ai-evals-runner](agents/ai-evals-runner.md) | subagent | Build and run evals |
| [llm-security-reviewer](agents/llm-security-reviewer.md) | subagent | Security review of LLM apps |

## Commands

`/ai-spec` · `/ai-build` · `/ai-evals` · `/ai-review` · `/ai-research` · `/ai-memory`

## Plugins

| Plugin | What it does |
|--------|-------------|
| `gates.ts` | **Blocks** commit without tests, secret files staged, secrets in outbound fetch/search |
| `memory.ts` | Captures errors→gotchas, commits→memory; injects recall into every session |
| `voice-guard.ts` | Flags output that reads like AI-generated text (dashes, AI vocabulary) |
| `verify-guard.ts` | Flags conjecture-as-grounding (`probably`, `should be`, `i assume`) per anti-delirium |

## Memory

SQLite + FTS5 + **local semantic embeddings** (fastembed/ONNX). The living feedback loop:
encode → consolidate → retrieve → reconsolidate. Auto-captures errors and agent findings;
recall is injected into every session. **100% local, never versioned.**
See [docs/MEMORY-SPEC.md](docs/MEMORY-SPEC.md).

---

## Model Policy

| Role | Model | Requests/mo | Cost/MTok out |
|------|-------|-------------|----------------|
| Default | `opencode-go/deepseek-v4-pro` | 17,150 | $0.87 |
| small_model | `opencode-go/deepseek-v4-flash` | 158,150 | $0.28 |

Routing rule: **reasoning to PRO, mechanical to FLASH**. Mode rule: **ambiguity or stakes
→ PLAN first, clear + approved → BUILD**. See [docs/MODEL-POLICY.md](docs/MODEL-POLICY.md).

---

## Repository Structure

```
llmfoundry/
├── agents/          # 5 agents (orchestrator + 4 specialists)
├── commands/        # 6 slash commands
├── skills/          # 20 skills (4 categories)
├── plugins/         # gates, memory, voice-guard, verify-guard
├── evals/           # golden-sets, rubric, baseline
├── docs/            # architecture, model policy, memory spec, RE spec
├── references/      # shared checklists
├── templates/       # sanitized MEMORY templates (placeholders only)
├── scripts/         # install.sh, memory engine, eval runner, routing scorer
├── .github/         # CI workflow
└── assets/          # logo
```

---

## Testing (regression gate)

The kit tests itself. `scripts/eval-runner.py` runs 27 deterministic checks (no model):
engine unit tests, routing golden-set validation, scorer cases, plugin compile checks.
A GitHub Actions CI runs them on every push/PR. Baseline: [evals/baseline.json](evals/baseline.json).

```bash
python3 scripts/eval-runner.py          # full suite
python3 scripts/eval-runner.py --baseline  # show the number to beat
```

---

## Documentation

| Doc | Covers |
|-----|--------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and data flow |
| [docs/MODEL-POLICY.md](docs/MODEL-POLICY.md) | Why DeepSeek, PRO/FLASH + BUILD/PLAN routing |
| [docs/MEMORY-SPEC.md](docs/MEMORY-SPEC.md) | Memory architecture, living loop, privacy |
| [docs/INSTALL.md](docs/INSTALL.md) | Full install/uninstall guide |
| [docs/REVERSE-ENGINEERING-SPEC.md](docs/REVERSE-ENGINEERING-SPEC.md) | Planned RE specialist |
| [SKILLS.md](SKILLS.md) | Skill catalog |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to add skills/agents/commands/evals |

---

## Roadmap

- [x] Core kit: skills, agents, commands, plugins, memory, evals
- [x] Orchestrator (the Captain) as default agent
- [x] Semantic memory (local embeddings)
- [x] Gates as real commit blockers
- [x] Routing eval (golden-set + deterministic scorer)
- [x] Regression CI (27 checks on every push)
- [x] Human-voice + anti-delirium disciplines
- [x] PRO/FLASH + BUILD/PLAN routing policies
- [ ] Agent stability baselines (K=5 runs)
- [ ] Reverse engineering specialist (see [SPEC](docs/REVERSE-ENGINEERING-SPEC.md))

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Follow the kit's own discipline:
SPEC → TDD → worktree → atomic commit.

## FAQ

**Do I need to pay for expensive models?** No, the kit is built for DeepSeek
(V4 Pro/Flash), which is 35-322x more requests per dollar than kimi-k3.

**Is my code/memory sent anywhere?** No. Memory is 100% local (SQLite + local embeddings),
never versioned. See [docs/MEMORY-SPEC.md](docs/MEMORY-SPEC.md).

**Does it work alongside my existing opencode setup?** Yes, the installer uses
`skills.paths` and per-file symlinks, coexisting with existing skills/agents.

**Is it only for opencode?** Built for opencode, but skills follow the Agent Skills open
standard (agentskills.io), portable to Claude Code, Codex, Cursor, etc.

**How does it prevent hallucination?** Every claim must have proof or a confidence marker
(`anti-delirium` skill + `verify-guard` plugin). The orchestrator verifies before asserting.

---

## License

MIT. See [LICENSE](LICENSE).
