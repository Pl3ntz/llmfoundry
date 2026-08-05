<!--
  LLMFoundry: AI engineering kit for DeepSeek.
  Keywords for search: AI engineering, LLM agents, RAG, MCP, prompt engineering,
  LLM evals, DeepSeek, opencode, AI agents toolkit, agent skills, quality gates,
  anti-delirium, human voice, orchestrator.
-->
<p align="center">
  <img src="assets/logo.svg" alt="LLMFoundry: AI engineering kit for DeepSeek" width="480">
</p>

<p align="center">
  <strong>Build LLM apps, agents, RAG, evals, and MCP with production discipline.</strong>
</p>

<p align="center">
  <a href="https://github.com/Pl3ntz/llmfoundry/releases"><img alt="Release" src="https://img.shields.io/github/v/release/Pl3ntz/llmfoundry"></a>
  <a href="https://github.com/Pl3ntz/llmfoundry"><img alt="GitHub" src="https://img.shields.io/github/stars/Pl3ntz/llmfoundry?style=social"></a>
  <a href="https://github.com/Pl3ntz/llmfoundry/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-lightgrey.svg"></a>
  <a href="docs/MODEL-POLICY.md"><img alt="Model" src="https://img.shields.io/badge/model-DeepSeek_V4_Pro-2ea44f.svg"></a>
  <a href="docs/CI-LOCAL.md"><img alt="CI" src="https://img.shields.io/badge/CI-VPS_cron_06--00-2ea44f.svg"></a>
  <a href="evals/baseline.json"><img alt="Tests" src="https://img.shields.io/badge/tests-44%2F44-2ea44f.svg"></a>
  <a href="skills/anti-delirium/"><img alt="Anti-delirium" src="https://img.shields.io/badge/discipline-anti--delirium-2ea44f.svg"></a>
  <a href="skills/human-voice/"><img alt="Human voice" src="https://img.shields.io/badge/discipline-human--voice-2ea44f.svg"></a>
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

<p align="center">
  <strong>Built for $2.01.</strong> The entire kit, 30 skills, 14 agents, memory, gates,
  44 tests, and full docs, developed on DeepSeek V4. This is what cost discipline buys.
</p>

> Looking for: AI agents, RAG pipeline, prompt engineering, LLM evals, MCP servers,
> DeepSeek coding, AI engineering best practices, agent skills for opencode? You're in the right place.

## See it in action

You send a rough idea. The orchestrator turns it into a plan, verifies instead of guessing,
and produces work you can trust. This is how it actually feels:

```text
You:  "I want an agent that pulls fresh docs for libraries and answers with sources"

Orch: Before I design this, I need one decision. What interface?
      A) CLI   B) web chatbot   C) API   D) MCP server inside opencode

You:  "D"

Orch: Good, an MCP server. Let me specify:
      SPEC: tech-docs-agent, scope, done criteria, out of scope.
      Delegating to ai-architect with full context...

      [ai-architect] returns a design with trade-offs
      [llm-security-reviewer] reviews prompt injection and exfiltration
      [deep-researcher-v2] validates the cited sources

Orch: 3 agents ran in parallel. Contradictions resolved.
      Here is the final plan, approved to implement.
```

**And every claim in that flow was verified, not guessed.** That is the LLMFoundry difference:
a team that reasons, delegates, checks its own work, and writes like a human.

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

That is it. Three commands and the kit is live in opencode.

The installer, in one pass:
- symlinks `agents/` and `commands/` into `~/.config/opencode/`
- registers `skills/` via `skills.paths`, so your existing skills stay untouched
- installs Python deps for the memory engine (fastembed for semantic search)
- registers the gates, memory, voice, and verify plugins in your opencode config

Restart opencode. The orchestrator becomes your default agent, and you are working with
a team instead of a single model.

```text
What you had:    one generic agent, prompt by prompt
What you get:    an orchestrator + 13 specialists + a memory that learns + gates that protect
```

> Requires: opencode, python3, DeepSeek V4 (Go plan or API key).
> Full guide in [docs/INSTALL.md](docs/INSTALL.md).

## The team

```
You ──→ AI Orchestrator (the Captain) ──→ specialist subagents
              │
              ├─ deep-researcher-v2      (deep research with correlation + anti-injection)
              ├─ ai-architect         (LLM system design with trade-offs)
              ├─ ai-evals-runner      (prove it works)
              ├─ llm-security-reviewer(security before shipping)
              ├─ reverse-engineer     (binary, firmware, malware analysis)
              ├─ red-team-agent       (authorized offensive security)
              ├─ bug-bounty-hunter    (scope to validated report)
              ├─ security-defensive   (defensive audit, hardening)
              ├─ database-engineer    (full PostgreSQL stack)
              ├─ data-model-engineer  (data modeling, tenancy)
              ├─ backend-architect    (API design, middleware, queues, caching)
              ├─ platform-engineer    (infra, Docker, CI/CD, cloud, monitoring)
              └─ api-contract-engineer(deep API contract work)
              │
              └─ Living Memory (SQLite + embeddings, self-feeding)
```

The flow: you send a raw idea → the orchestrator **captures intent**, asks one question at
a time until it understands → defines the **SPEC** with you → **rewrites** into a master
prompt → **delegates** with full context → **synthesizes** results and presents options.

---

## Skill Catalog

30 skills in 5 categories. All follow the transversal standards.

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

### Reverse Engineering
| Skill | Use when |
|-------|----------|
| `re-binary-analysis` | Identify format, arch, packing |
| `re-decompilation` | Recover logic from disassembly (radare2/Ghidra) |
| `re-algorithm-recovery` | Reconstruct crypto/checksums/serials with proof |
| `re-dynamic-analysis` | Confirm behavior under controlled execution |
| `re-malware-analysis` | Malware triage, IOC extraction, safe detonation |
| `re-firmware-analysis` | Extract and analyze device firmware |
| `pdf-processing` | Fast local PDF to text/Markdown (pdf-inspector, MIT, free) |

Full catalog: [SKILLS.md](SKILLS.md)

---

## Agents

| Agent | Mode | Role |
|-------|------|------|
| [ai-orchestrator](agents/ai-orchestrator.md) | primary (default) | The Captain, interprets, discusses, delegates, synthesizes |
| [deep-researcher-v2](agents/deep-researcher-v2.md) | subagent | Deep research with correlation + anti-injection |
| [ai-architect](agents/ai-architect.md) | subagent | LLM system architecture with trade-offs |
| [ai-evals-runner](agents/ai-evals-runner.md) | subagent | Build and run evals |
| [llm-security-reviewer](agents/llm-security-reviewer.md) | subagent | Security review of LLM apps |
| [reverse-engineer](agents/reverse-engineer.md) | subagent | Binary, firmware, malware analysis |
| [red-team-agent](agents/red-team-agent.md) | subagent | Enterprise red team, pentest, exploitation |
| [bug-bounty-hunter](agents/bug-bounty-hunter.md) | subagent | Bug bounty, web and API hunting |
| [security-defensive](agents/security-defensive.md) | subagent | Defensive audit, hardening, remediation |
| [database-engineer](agents/database-engineer.md) | subagent | Full PostgreSQL: schema, indexes, EXPLAIN, RLS, migrations |
| [data-model-engineer](agents/data-model-engineer.md) | subagent | Data modeling, normalization, partitioning, tenancy |
| [backend-architect](agents/backend-architect.md) | subagent | Backend design: APIs, middleware, jobs, caching, queues |
| [api-contract-engineer](agents/api-contract-engineer.md) | subagent | Deep API contracts: OpenAPI discriminators, hypermedia, rate limit RFCs |
| [platform-engineer](agents/platform-engineer.md) | subagent | Infrastructure: Terraform, Docker, K8s, CI/CD, cloud, monitoring |

## Commands

`/ai-spec` · `/ai-build` · `/ai-evals` · `/ai-review` · `/ai-research` · `/ai-memory` · `/ai-re`

## Plugins

| Plugin | What it does |
|--------|-------------|
| `gates.ts` | **Blocks** commit without tests, secret files staged, secrets in outbound fetch/search |
| `memory.ts` | Captures errors→gotchas, commits→memory; injects recall into every session |
| `voice-guard.ts` | Flags output that reads like AI-generated text (dashes, AI vocabulary) |
| `verify-guard.ts` | Flags conjecture-as-grounding (`probably`, `should be`, `i assume`) per anti-delirium |
| `publish-guard.ts` | Injects mandatory human-voice + anti-delirium + standards gate into every system prompt |
| `delegation-guard.ts` | Validates subagent spawns: 4 mandatory parts + routing table check |
| `research-guard.ts` | Warns only when the ORCHESTRATOR fetches research directly; subagents (deep-researcher-v2) research freely |

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
├── agents/          # 14 agents (orchestrator + 13 specialists)
├── commands/        # 7 slash commands
├── skills/          # 30 skills (5 categories)
├── plugins/         # 7 plugins: gates, memory, voice-guard, verify-guard, publish-guard, delegation-guard, research-guard
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

The kit tests itself. `scripts/eval-runner.py` runs 44 deterministic checks, no model
calls: engine unit tests, routing golden-set validation, scorer cases, plugin compile
checks, and K=5 stability checks. A GitHub Actions CI runs them on every push/PR, so a
regression is caught before it ships. Baseline: [evals/baseline.json](evals/baseline.json).

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
| [docs/CI-LOCAL.md](docs/CI-LOCAL.md) | CI na VPS via Docker + cron, sem GitHub Actions |
| [docs/REVERSE-ENGINEERING-SPEC.md](docs/REVERSE-ENGINEERING-SPEC.md) | Reverse engineering specialist design |
| [SKILLS.md](SKILLS.md) | Skill catalog |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to add skills/agents/commands/evals |

---

## Roadmap

- [x] Core kit: skills, agents, commands, plugins, memory, evals
- [x] Orchestrator (the Captain) as default agent
- [x] Semantic memory (local embeddings)
- [x] Gates as real commit blockers
- [x] Routing eval (golden-set + deterministic scorer, validated manually)
- [x] Regression CI (44 checks on every push)
- [x] Human-voice + anti-delirium disciplines
- [x] PRO/FLASH + BUILD/PLAN routing policies
- [x] Stability checks (K=5, deterministic engine)
- [x] Reverse engineering specialist (6 skills + agent + command)
- [x] Recall includes memories + facts (not just findings/gotchas) so imported knowledge enters agent context automatically
- [x] Fleet redesign: database-engineer, backend-architect, platform-engineer, security-defensive (14 agents, balanced coverage)
- [x] Publish guard: mandatory human-voice + anti-delirium + standards gate on every system prompt
- [x] Delegation guard: validate subagent spawns (4 mandatory parts + routing table)
- [x] Research guard: enforce research delegation policy (no direct webfetch from orchestrator)

> Routing is validated manually, one question at a time, to avoid batch sessions
> touching the user's Chrome. Batch automation of model-routing tests was removed.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Follow the kit's own discipline:
SPEC → TDD → worktree → atomic commit.

## How we compare

Honest numbers, sourced from a live deep-researcher-v2 pass over GitHub and npm (Aug 2026).

| Project | Stars | Focus | Gates | Anti-delirium | Evals | DeepSeek-first |
|---------|-------|-------|-------|---------------|-------|----------------|
| **LLMFoundry** | new | complete kit for opencode | ✅ runtime plugins | ✅ | ✅ 44 checks | ✅ |
| agent-skills (addyosmani) | 81.2k | skills pack (multi-tool) | ⚠️ prompt-based | ✅ | ✅ evals/ | ❌ |
| hiai-opencode | 12 | multi-agent + gates | ✅ runtime | ❌ | ✅ 986 tests | ❌ |
| GoopSpec | 37 | spec-driven workflow | ✅ contract gates | ❌ | ❌ | ❌ |
| CrewBee | 16 | agent teams | ⚠️ reviewer | ❌ | ❌ | ❌ |
| maestria | 2 | cross-IDE management | ⚠️ guidance only | ❌ | ❌ | ❌ |

What no competitor combines: **DeepSeek-first cost, an orchestrator + 13 specialists,
living semantic memory, runtime quality gates, anti-delirium, and human-voice in one
install for opencode.** agent-skills is the closest in quality, but it is a skills pack,
not a team with memory and gates, and it is not cost-optimized for DeepSeek.

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
