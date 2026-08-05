# LLMFoundry Memory: SPEC v1

**Status:** Implemented
**Author:** vplentz
**Date:** 2026-08-01
**Name:** LLMFoundry Memory (working name: `foundry-memory`)
**Complexity:** Complex

---

## What

A unified continuous-learning memory system for LLMFoundry. Captures structured
knowledge from sessions (resolved errors, decisions, recurring patterns, agent findings)
with search, confidence, reinforcement, and promotion, forming a living loop that the
structure itself feeds and consumes.

## Why

An agent without memory starts from zero every session. LLMFoundry memory keeps what was
learned, reuses decisions, avoids repeating mistakes, and speeds up work. It is 100%
local, never versioned, focused on opencode + DeepSeek + AI engineering.

### Features

| Feature | Detail |
|---------|--------|
| FTS5 full-text search | lexical search with porter stemming |
| Local embeddings (semantic) | intent-based search, not just tokens |
| Confidence + reinforcement | facts gain weight when re-confirmed |
| Severity/status on findings | actionable memory, not just text |
| Per-project container | isolation by context |
| Recurrence with promotion | gotchas become rules (3+ occurrences) |
| Hook-driven capture | automatic, not manual |

### Design decisions

| Decision | Reason |
|-----------|---------------------|
| `recall_log` with action confirmation | capture without measurable use is noise |
| Lexical-only first, embeddings v2 | embeddings layer on top of the structured data |
| Raw turns are noise | **Structured capture**: only events with signal |
| No expiration/decay | temporal decay + archival |
| No measurable auto-promotion | promotion gate with explicit criteria |
| Proprietary store hard to version | curated markdown layer, git-friendly |

---

## Storage decision (based on our setup)

**Our reality:** opencode + DeepSeek (cheap, we want to maximize use) + git-versionable
kit. Structured capture = low volume, high signal.

**Decision: SQLite (live storage) + curated Markdown (LOCAL, never versioned).**

| Layer | Technology | Role |
|--------|-----------|-------|
| **Live** | SQLite + FTS5 | structured event store, lexical search, metrics |
| **Curated** | Markdown in `~/.local/share/llmfoundry/memory/` per project | what survives the session, **100% local, never in git** |
| **Semantic** | Embeddings (v2, optional) | vector correlation over the curated layer |

> **PRIVACY (inviolable rule):** memory is **local-only, never versioned**.
> The LLMFoundry repo (versioned/shared) contains **ONLY empty templates** with
> placeholders. No real memory, business rule, personal data, secret, client name, or
> proprietary snippet enters the repo. Captured content lives in
> `~/.local/share/llmfoundry/memory/` (outside the repo) or in `.llmfoundry/` gitignored
> per project.

**Why no embeddings in v1:**
1. Structured capture = low volume, FTS5 lexical search covers it.
2. Embeddings add API cost (embedding models), against the cheap-DeepSeek philosophy.
3. Vectors are not portable/versionable; the curated local layer is plain markdown.
4. v2 can add sqlite-vec without rewriting anything.

**Privacy (justification):** memory holds decisions, gotchas, and findings from real
work, content that must not leave the machine or the repo. Versioning memory risks
leaking business rules or personal data into a shared repo. So the curated layer is local
and the repo ships only sanitized templates.

**Why not just files:**
- Structured queries (severity, status, count, confidence) beat loose text.
- SQLite is local, serverless, no infra, same as the setup.

---

## Architecture: memory as a living loop (not a passive store)

Memory is not a database you write to and forget. It is a **feedback cycle** the LLMFoundry
structure feeds and consumes, like human memory.

```
        ┌──────────────────────────────────────────────────────┐
        │                  MEMORY LIVING LOOP                  │
        │                                                       │
        │  AGENTS/SKILLS/COMMANDS/PLUGINS                       │
        │    (deep-researcher, llm-security-reviewer,           │
        │     ai-architect, ai-evals-runner, hooks, /ai-*)      │
        │         │                      ▲                      │
        │   FEEDS (encode)         CONSUMES (retrieve)          │
        │         ▼                      │                      │
        │  ┌─────────────┐         ┌─────────────┐              │
        │  │  MEMORY     │◄────────│  CONTEXT    │              │
        │  │  (SQLite +  │ injects │  injected   │              │
        │  │  FTS5 + MD) │ into    │  into       │              │
        │  │             │ prompt  │  prompt     │              │
        │  └─────────────┘         └─────────────┘              │
        │         │                      │                      │
        │    NORMALIZE               REINFORCE                 │
        │    DEDUP/DECAY             (recall use =             │
        │    CONSOLIDATE             reinforces weight)        │
        │         └──────────┬───────────┘                      │
        │                    ▼                                  │
        │             BETTER DECISIONS →                        │
        │             more findings/gotchas → back to the top   │
        └──────────────────────────────────────────────────────┘
```

### The 4 phases (like human memory)

| Phase | Mechanism | In the structure |
|------|-----------|--------------|
| **Encode** | the structure captures what it learned | `tool.execute.after` hooks, agent findings, `/ai-memory remember`, SPEC decisions |
| **Consolidate** | normalize, dedup, reinforce, decay | gotcha hashes, `confidence++`, temporal decay |
| **Retrieve** | the structure fetches what it needs | recall before spawning an agent (`---memory---` preamble), skills inject context, `recall_log` |
| **Reconsolidate** | used recall reinforces, unused decays | `acted_on` (was it acted on?) → reinforce or archive |

### The loop rule: nothing feeds or is fed in isolation

1. **Every agent in the kit** feeds memory (findings) AND consults it (preamble) before
   acting. Without injected `---memory---`, the agent operates with no memory.
2. **Every transversal skill** (ai-engineering-standards, ai-dev-process) consults
   relevant decisions and gotchas.
3. **Commands** (`/ai-*`) record decisions and read history.
4. **Recall is observable**: `recall_log` proves memory was consumed and acted on, not
   just captured.
5. **Memory feeds the prompt** (retrieve), never the reverse: a prompt never becomes raw
   memory; memory is always structured consolidation.

---

## Scope: Subsystems

### 1. Capture (structured, hook-driven)

Capture **events with signal**, not turns:

| Event | Trigger | Example |
|--------|---------|---------|
| **Resolved error** | `tool.execute.after` (bash failed, then ok) | "build error X fixed by Y" |
| **Decision** | `/ai-memory remember` or SPEC-flow detection | "chose DeepSeek V4 Pro over kimi-k3 on cost" |
| **Recurring pattern** | gotcha count >= 3 | "npm install always runs as sudo" |
| **Agent finding** | agents with findings (deep-researcher, llm-security-reviewer) | "[HIGH] SSRF via fetch tool, fix at X" |
| **Static fact** | manual | "project uses FastAPI + raw SQL, no ORM" |

Implementation: opencode plugin (`plugins/memory.ts`) on `tool.execute.after` hooks +
`/ai-memory remember|forget|search|stats` commands.

### 2. Data model (SQLite)

```
memories: structured events (type, content, container, metadata JSON)
memory_fts: FTS5 (content)
memory_facts: profile facts with confidence + reinforced_count
gotchas: patterns with hash + count + samples + promoted
findings: agent findings (severity, status, acted_on)
recall_log: recall with acted_on (proves it was consumed and acted on)
session_metrics: per-session metrics
```

### 3. Memory lifecycle

```
CAPTURE (hook/command)
  → NORMALIZE (dedup by hash, count)
  → REINFORCE (confidence++ when re-observed)
  → DECAY (weight drops over time if not reinforced)
  → PROMOTE (>=3 recurrences + 5 matrix criteria → MEMORY/*.md LOCAL)
  → ARCHIVE (unused for 90 days → moved, not deleted)
```

> Promotion writes to the local layer (`~/.local/share/llmfoundry/memory/<project>/`),
> never to the repo. The repo keeps only `templates/MEMORY/` with empty examples.

**Promotion Criteria Matrix:**
Recurrence >=3 sessions · Consistency (same solution) · Impact (prevented an error / saved
time) · Stability (system unchanged) · Clarity (1-2 sentences, <=200 chars).

### 4. Curated layer (LOCAL, never versioned)

Local: `~/.local/share/llmfoundry/memory/<project>/`

```
MEMORY/
├── PROJECT.md        # static project facts
├── DECISIONS.md      # light ADRs (decision, why, when)
├── GOTCHAS.md        # promoted patterns with fixes
├── FINDINGS.md       # open/resolved findings
└── INDEX.md          # summary + stats
```

**Golden rule:** this layer is **100% local**. If a project needs versioned memory, use
`.llmfoundry/` in that repo, **gitignored**, never in git history and never in the shared
repo.

The LLMFoundry repo keeps only `templates/MEMORY/`, the same shape with **empty examples
and placeholders**, for the user to copy into the local layer. No real content.

### 5. Recall with confirmation

- Recall happens when a skill/agent consumes a memory.
- `recall_log` records: what was recalled, by whom, and **acted_on** (was it acted on?).
- If a finding is recalled 2x without action, its priority rises or it is marked stale.

---

## Out of scope (v1)

- Embeddings/semantic search (v2)
- Memory MCP server (not needed, SQLite covers it)
- Raw turn capture (rejected, noise)
- Multi-machine sync (out of scope, curated layer is local)

---

## Success criteria

1. Automatic capture of resolved errors and agent findings (hook)
2. `recall_log` with `acted_on` populated, memory provably consumed and acted on
3. Promotion requires 5 criteria; nothing auto-promotes without the matrix
4. Curated markdown layer **100% local**, repo contains only empty templates
5. FTS5 search + filters (type, severity, project)
6. Zero server dependency, all local
7. Uses < 100 DeepSeek API requests/month (capture does not depend on LLM)

## Privacy criteria (inviolable)

1. **No real memory enters the repo.** Repo = only `templates/MEMORY/` with placeholders.
2. **Zero business rules, personal data, secrets, client names** in any versioned artifact.
3. SQLite and curated markdown in `~/.local/share/llmfoundry/` or `.llmfoundry/`, both
   outside git.
4. LLMFoundry `.gitignore` blocks `.llmfoundry/`, `memory/`, `*.db` by default.
5. `install.sh` never copies memory, only sanitized templates.
6. Any content detected as PII/secret during capture is discarded or obscured before
   persisting locally.

---

## Integration with the kit (the loop in practice)

Each component has a dual role: **feeds** (encode) and **consumes** (retrieve).

| Component | FEEDS (encode) | CONSUMES (retrieve) |
|-----------|-------------------|--------------------|
| `plugins/memory.ts` | `tool.execute.after` hooks, resolved errors, gotchas | (it is the loop runtime) |
| `commands/ai-memory.md` | `/ai-memory remember` | `/ai-memory search` |
| `agents/deep-researcher.md` | findings into `findings` (severity, status) | `---memory---` preamble before researching (past decisions) |
| `agents/llm-security-reviewer.md` | security findings | recall of previous open findings |
| `agents/ai-architect.md` | architecture decisions into `DECISIONS.md` | past project decisions |
| `agents/ai-evals-runner.md` | eval baselines | regression history |
| `skills/ai-engineering-standards` | none | relevant gotchas + decisions |
| `skills/ai-dev-process` | none | project patterns (past SPECs) |
| `skills/ai-research` | none | past research findings (do not re-search what is settled) |
| `evals/` | session_metrics | (not used as eval data) |

**Execution rule:** every agent in the kit MUST receive the recall (`---memory---`)
before acting and MUST record what it learned afterward. Without this, the loop does not
close.

---

## Implementation plan

1. `scripts/memory/`: Python/SQLite module (schema, insert, search, promote, decay, recall)
2. `plugins/memory.ts`: capture hooks + recall injection
3. `commands/ai-memory.md`: CLI surface (remember|search|forget|stats|promote|recall)
4. Local `MEMORY/*.md` templates (sanitized placeholders)
5. Recall integration in the agents (`---memory---` preamble)
6. Test: real session, verify encode → retrieve → acted_on → reinforcement
7. Commit + version
