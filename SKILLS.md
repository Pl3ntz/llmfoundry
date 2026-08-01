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

## Agents

| Agent | Use when |
|-------|----------|
| [ai-orchestrator](agents/ai-orchestrator.md) | **Default.** The Captain, interprets, discusses, delegates, synthesizes |
| [deep-researcher](agents/deep-researcher.md) | Deep research with correlation |
| [ai-architect](agents/ai-architect.md) | Designing LLM system architecture |
| [ai-evals-runner](agents/ai-evals-runner.md) | Building and running evals |
| [llm-security-reviewer](agents/llm-security-reviewer.md) | Security review before shipping |

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
