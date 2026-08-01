<p align="center">
  <img src="assets/logo.svg" alt="LLMFoundry" width="480">
</p>

# LLMFoundry

The AI engineering kit for DeepSeek. Skills, standards, and quality gates for building
LLM systems — agents, RAG, evals, MCP — with production discipline: **SPEC → TDD → worktree → atomic commit**.

[![Skills](https://img.shields.io/badge/skills-18-0366d6.svg)](#skill-catalog)
[![Agents](https://img.shields.io/badge/agents-5-0366d6.svg)](#agents)
[![Commands](https://img.shields.io/badge/commands-6-0366d6.svg)](#commands)
[![Plugins](https://img.shields.io/badge/plugins-2-0366d6.svg)](#plugins)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)
[![Model](https://img.shields.io/badge/model-DeepSeek_V4_Pro-2ea44f.svg)](docs/MODEL-POLICY.md)

---

## What is LLMFoundry?

**LLMFoundry** is a complete kit to develop production-quality LLM applications on top of
**DeepSeek** (cheap, high-volume) with engineering discipline. It turns opencode into a
team: an **orchestrator** that understands your intent and delegates to specialist agents,
a **living memory** that learns and feeds itself, and **gates** that block bad output.

### The team

```
You ──→ AI Orchestrator (the Captain) ──→ specialist subagents
              │
              ├─ deep-researcher      (deep research with correlation)
              ├─ ai-architect         (LLM system design)
              ├─ ai-evals-runner      (prove it works)
              └─ llm-security-reviewer(security before shipping)
              │
              └─ Living Memory (SQLite + embeddings, self-feeding)
```

### The flow

1. **You** send a raw idea (even vague) to the orchestrator
2. It **captures intent**, asks one question at a time until it understands
3. It defines the **SPEC** with you, then **rewrites** into a master prompt
4. It **delegates** to the right subagents with full context
5. It **synthesizes** results and presents options for you to decide

### Principles

1. **English** — everything in English.
2. **DeepSeek-optimized** — imperative tone, minimal guardrails, no hedging. Explicit
   structures compensate for lower guardrails.
3. **Engineering standards** — verifiable output (`file:line`, command+output, schema).
4. **Mandatory dev process** — SPEC → TDD → git worktree → atomic commit.
5. **Privacy by design** — memory is 100% local, never versioned.

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
- configures the gates + memory plugins

Then restart opencode. The orchestrator becomes your default agent.

> Requires: opencode, python3, DeepSeek V4 (Go plan or API key).
> See [docs/INSTALL.md](docs/INSTALL.md) for details.

---

## Skill Catalog

18 skills in 3 categories. All follow the transversal standards.

### Dev Process (transversal)
| Skill | Use when |
|-------|----------|
| `ai-engineering-standards` | Start of every task — tone, evidence, anti-fabrication |
| `ai-dev-process` | Writing code — SPEC, worktree, TDD, atomic commit |
| `interview-me` | Request is underspecified or high-stakes |
| `ai-orchestration` | Routing, delegation protocol, fan-in synthesis |

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
| `doubt-driven-development` | High-stakes review — CLAIM/EXTRACT/DOUBT/RECONCILE |
| `source-driven-development` | Grounding decisions in official docs |
| `debugging-and-error-recovery` | 5-step debugging |

Full catalog with descriptions: [SKILLS.md](SKILLS.md)

---

## Agents

| Agent | Mode | Role |
|-------|------|------|
| [ai-orchestrator](agents/ai-orchestrator.md) | primary (default) | The Captain — interprets, discusses, delegates, synthesizes |
| [deep-researcher](agents/deep-researcher.md) | subagent | Deep research with correlation + anti-injection |
| [ai-architect](agents/ai-architect.md) | subagent | LLM system architecture with trade-offs |
| [ai-evals-runner](agents/ai-evals-runner.md) | subagent | Build and run evals |
| [llm-security-reviewer](agents/llm-security-reviewer.md) | subagent | Security review of LLM apps |

## Commands

`/ai-spec` · `/ai-build` · `/ai-evals` · `/ai-review` · `/ai-research` · `/ai-memory`

## Plugins (gates)

| Plugin | Refuses when |
|--------|-------------|
| `gates.ts` | commit without tests, secret files staged, secrets in outbound fetch/search |
| `memory.ts` | — (captures errors→gotchas, commits→memory; injects recall into prompts) |

## Memory

SQLite + FTS5 + **local semantic embeddings** (fastembed/ONNX). The living feedback loop:
encode → consolidate → retrieve → reconsolidate. Auto-captures errors and agent findings;
recall is injected into every session. **100% local, never versioned.**

---

## Model Policy

| Role | Model | Requests/mo | Cost/MTok out |
|------|-------|-------------|----------------|
| Default | `opencode-go/deepseek-v4-pro` | 17,150 | $0.87 |
| small_model | `opencode-go/deepseek-v4-flash` | 158,150 | $0.28 |

Cost decision: DeepSeek family over kimi-k3 (53x cheaper, 35-322x more requests).
See [docs/MODEL-POLICY.md](docs/MODEL-POLICY.md).

---

## Repository Structure

```
llmfoundry/
├── agents/          # 5 agents (orchestrator + 4 specialists)
├── commands/        # 6 slash commands
├── skills/          # 18 skills
├── plugins/         # gates.ts + memory.ts
├── evals/           # golden-set + rubric (deep-researcher)
├── docs/            # architecture, model policy, memory spec
├── references/      # shared checklists
├── templates/       # sanitized MEMORY templates (placeholders only)
├── scripts/         # install.sh + memory engine
└── assets/          # logo
```

---

## Documentation

| Doc | Covers |
|-----|--------|
| [docs/MEMORY-SPEC.md](docs/MEMORY-SPEC.md) | Memory architecture, living loop, privacy |
| [docs/MODEL-POLICY.md](docs/MODEL-POLICY.md) | Why DeepSeek, cost comparison |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and flow |
| [docs/INSTALL.md](docs/INSTALL.md) | Full install guide |
| [SKILLS.md](SKILLS.md) | Skill catalog |

---

## Roadmap (parity with Quarterdeck, then beyond)

- [x] Core kit: skills, agents, commands, plugins, memory, evals
- [x] Orchestrator (the Captain) as default agent
- [x] Semantic memory (local embeddings)
- [ ] Gates tested as real commit blockers
- [ ] Routing eval (measure orchestrator routing quality)
- [ ] Agent stability baselines (K=5 runs)
- [ ] GitHub Actions CI for evals

---

## License

MIT. See [LICENSE](LICENSE).
