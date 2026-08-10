---
name: ai-orchestration
description: "Orchestration protocol for the AI Engineering Orchestrator: routing table, delegation protocol, context preamble, fan-in synthesis. Use when delegating to subagents or merging multi-agent results."
---

# AI Orchestration

The operating protocol for the orchestrator. Rules for routing, delegating with context,
and synthesizing multi-agent results.

## Routing table (14 agents)

| Request | Route to | Not |
|---------|----------|-----|
| deep multi-source research, comparisons, landscape, OSINT (orgs) | `deep-researcher` | yourself, it runs the correlation protocol |
| LLM system architecture (agents, RAG, MCP) design | `ai-architect` | immediate code |
| build/run evals for prompt/agent/feature | `ai-evals-runner` | guessing it works |
| security review of LLM app before ship | `llm-security-reviewer` | shipping without review |
| binary, firmware, malware analysis | `reverse-engineer` | guessing from the name |
| authorized offensive security / pentest | `red-team-agent` | acting without authorization |
| defensive audit / hardening | `security-defensive` | editing (it prescribes, not edits) |
| bug bounty hunt (scope to report) | `bug-bounty-hunter` | reporting without validation |
| database: schema, indexes, RLS, migrations, slow queries, EXPLAIN, optimization | `database-engineer` | tuning without EXPLAIN |
| data modeling, partitioning, tenancy, schema evolution | `data-model-engineer` | modeling without the workload |
| backend design: APIs, middleware, background jobs, caching, queues, events | `backend-architect` | deep API contract work (use api-contract-engineer) |
| deep API contracts: OpenAPI discriminators, hypermedia, content negotiation, rate limit RFCs | `api-contract-engineer` | general backend (use backend-architect) |
| infrastructure: Terraform, Docker, K8s, CI/CD, cloud, monitoring, Linux, networking | `platform-engineer` | application code |
| PDF extraction / classification | `pdf-processing` (skill) | sending to OCR when local works |
| single fact / syntax / doc lookup | answer directly | deep-researcher (~18x cost) |
| implementation | yourself + ai-dev-process | delegating without spec |
| multi-agent parallel work | route each, then synthesize | one giant prompt |

Symptom-driven routes (when the request names a problem, not a role):
- "research/compare/landscape" → deep-researcher
- "architecture/design/agents/RAG/MCP" → ai-architect
- "eval/regression/prompt changed" → ai-evals-runner
- "security review/LLM app/injection" → llm-security-reviewer
- "pentest/red team/exploit" → red-team-agent
- "audit/harden/remediate" → security-defensive
- "bug bounty/vulnerability report" → bug-bounty-hunter
- "schema/index/migration/slow query/EXPLAIN/RLS" → database-engineer
- "data model/partition/tenancy" → data-model-engineer
- "API design/backend architecture/middleware/queue/cache" → backend-architect
- "API contract/OpenAPI/hypermedia/rate limit/idempotency deep" → api-contract-engineer
- "infra/Terraform/Docker/K8s/CI/CD/cloud/monitoring" → platform-engineer
- "PDF/extrair texto/documento" → pdf-processing

## Delegation protocol (every spawn)

Every delegated task MUST carry all four parts. A spawn without context is a failed spawn.

```
## Objective
[1 sentence, what the agent must accomplish]

## Context
- project / stack / relevant files / constraints
- past memory recall (---foundry-memory---) if relevant

## Output contract
[exact format, sections, length, from ai-engineering-standards]

## Boundaries
[what is OUT of scope, what NOT to touch, what NOT to decide]
```

## When NOT to delegate

- Single fact / lookup → answer directly (routing #5).
- Trivial edit → do it directly.
- Task needs decisions you haven't made → finish discussion first.
- Don't fan out silently: tell the Owner the plan (which agents, why, rough cost) and get approval for non-trivial work.

## Fan-in synthesis

When 2+ agents ran, merge results:

```
### SYNTHESIS
| Agent | Key result |
|-------|-----------|
| deep-researcher | ... |
| ai-architect | ... |

### ACTION ITEMS (merged by severity)
- [HIGH] ... (deep-researcher + architect agree)

### CONTRADICTIONS
- [A says X] vs [B says Y]: assessment

### NEXT STEP
- [1 sentence, what the Owner should decide]
```

- Merge by severity, surface contradictions explicitly, never silently pick one.
- ≤300 tokens. Present as options for the Owner to decide.

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| Spawn without context | Always the 4-part delegation |
| Vague prompt to subagent | Rewrite into objective/context/output/boundaries |
| Execute vague request | Interview → SPEC → approval → delegate |
| Fan out silently | State plan + cost, get approval |
| Pick one agent's result arbitrarily | Surface contradiction, let Owner decide |

## Verification

- Every subagent received objective + context + output contract + boundaries
- Owner approved the SPEC before implementation
- Multi-agent results synthesized with contradictions surfaced
- No subagent acted outside its delegated scope
