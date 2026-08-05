# LLMFoundry Skill Catalog

17 skills organized in 3 categories. All skills follow the transversal standards
(`ai-engineering-standards`) and the mandatory dev process (`ai-dev-process`).

## Category A: Dev Process (transversal, inherited by all)

| Skill | Use when |
|-------|----------|
| [ai-engineering-standards](skills/ai-engineering-standards/) | Start of every task, tone, evidence discipline, anti-fabrication, output contract |
| [ai-dev-process](skills/ai-dev-process/) | Writing any code: SPEC, worktree, TDD, verify, atomic commit |
| [interview-me](skills/interview-me/) | Request is underspecified or high-stakes |
| [git-workflow](skills/git-workflow/) | Committing, branching, merging, resolving conflicts |
| [pull-request](skills/pull-request/) | Creating and updating effective PRs |
| [code-review](skills/code-review/) | Extremely effective review, five-axis method, before merge |

## Category B: AI Core

| Skill | Use when |
|-------|----------|
| [ai-prompt-engineering](skills/ai-prompt-engineering/) | Writing or iterating prompts |
| [ai-agent-patterns](skills/ai-agent-patterns/) | Designing agentic systems |
| [ai-context-engineering](skills/ai-context-engineering/) | Managing context windows |
| [ai-rag-pipeline](skills/ai-rag-pipeline/) | Building retrieval systems |
| [ai-evals](skills/ai-evals/) | Proving behavior, guarding regressions |
| [ai-model-integration](skills/ai-model-integration/) | Wiring providers, streaming, fallback |
| [ai-mcp-development](skills/ai-mcp-development/) | Building MCP servers |
| [ai-agent-safety](skills/ai-agent-safety/) | Sandboxing, permissions, fail-closed |
| [ai-llm-app-security](skills/ai-llm-app-security/) | Defensive LLM security (OWASP LLM Top 10) |
| [ai-llm-observability](skills/ai-llm-observability/) | Tracing, cost/token tracking |

## Category C: AI Advanced

| Skill | Use when |
|-------|----------|
| [ai-research](skills/ai-research/) | Deep research with correlation, multi-source, confidence-scored |
| [doubt-driven-development](skills/doubt-driven-development/) | High-stakes review: CLAIM/EXTRACT/DOUBT/RECONCILE |
| [source-driven-development](skills/source-driven-development/) | Grounding decisions in official docs |
| [debugging-and-error-recovery](skills/debugging-and-error-recovery/) | 5-step debugging: reproduce→localize→reduce→fix→guard |

### Reverse Engineering
| Skill | Use when |
|-------|----------|
| [re-binary-analysis](skills/re-binary-analysis/) | Identify format, arch, packing before deeper work |
| [re-decompilation](skills/re-decompilation/) | Recover logic from disassembly (radare2/Ghidra) |
| [re-algorithm-recovery](skills/re-algorithm-recovery/) | Reconstruct crypto, checksums, serial logic with proof |
| [re-dynamic-analysis](skills/re-dynamic-analysis/) | Confirm behavior under controlled execution |
| [re-malware-analysis](skills/re-malware-analysis/) | Malware triage, IOC extraction, safe detonation |
| [re-firmware-analysis](skills/re-firmware-analysis/) | Extract and analyze device firmware |
| [pdf-processing](skills/pdf-processing/) | Fast local PDF to text/Markdown (pdf-inspector, MIT, free) |

## Agents

| Agent | Use when |
|-------|----------|
| [ai-orchestrator](agents/ai-orchestrator.md) | **Default.** The Captain, interprets, discusses, delegates, synthesizes |
| [deep-researcher](agents/deep-researcher.md) | Deep research with correlation |
| [ai-architect](agents/ai-architect.md) | Designing LLM system architecture |
| [ai-evals-runner](agents/ai-evals-runner.md) | Building and running evals |
| [llm-security-reviewer](agents/llm-security-reviewer.md) | Security review before shipping |
| [reverse-engineer](agents/reverse-engineer.md) | Binary, firmware, and malware analysis with precision |
| [red-team-agent](agents/red-team-agent.md) | Authorized offensive security, enterprise red team |
| [bug-bounty-hunter](agents/bug-bounty-hunter.md) | Bug bounty: web, API, platform-specific hunting |
| [security-defensive](agents/security-defensive.md) | Defensive audit, hardening, remediation |
| [database-engineer](agents/database-engineer.md) | Full PostgreSQL stack: schema, indexes, EXPLAIN, RLS, migrations, query optimization |
| [data-model-engineer](agents/data-model-engineer.md) | Data modeling, normalization, partitioning, tenancy |
| [backend-architect](agents/backend-architect.md) | Backend design: APIs, middleware, jobs, caching, queues, event-driven |
| [api-contract-engineer](agents/api-contract-engineer.md) | Deep API contract work: OpenAPI discriminator, hypermedia, rate limit RFCs |
| [platform-engineer](agents/platform-engineer.md) | Infrastructure: Terraform, Docker, K8s, CI/CD, cloud, monitoring, Linux |

## Orchestration

| Skill | Use when |
|-------|----------|
| [ai-orchestration](skills/ai-orchestration/) | Routing, delegation protocol, fan-in synthesis |
| [human-voice](skills/human-voice/) | Write in a natural human voice, never looks AI-generated |
| [anti-delirium](skills/anti-delirium/) | Prove it or don't say it, evidence or confidence marker on every claim |

## Commands

`/ai-spec` · `/ai-build` · `/ai-evals` · `/ai-review` · `/ai-research`

## Eval harness

- [deep-researcher](evals/deep-researcher/), golden set + rubric (factual, myth,
  current-events, false-premise, OSINT). Run before changing the research agent.
