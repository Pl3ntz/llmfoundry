# LLMFoundry Architecture

How the kit fits together.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        OPENCODE                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           AI ORCHESTRATOR (default agent)           │    │
│  │  capture → discuss → define → rewrite → delegate    │    │
│  └───────────┬─────────────────────────────┬──────────┘    │
│              │                             │               │
│   ┌──────────▼──────────┐      ┌───────────▼──────────┐    │
│   │   SUBAGENTS (13)    │      │   MEMORY (loop)      │    │
│   │  deep-researcher    │      │  SQLite + FTS5       │    │
│   │  ai-architect       │      │  + embeddings        │    │
│   │  ai-evals-runner    │◄────►│  encode→consolidate  │    │
│   │  llm-security-      │ feed │  →retrieve→reconsol. │    │
│   │  reviewer           │ recall│                     │    │
│   │  reverse-engineer   │      │                      │    │
│   │  red-team-agent     │      │                      │    │
│   │  bug-bounty-hunter  │      │                      │    │
│   │  security-defensive │      │                      │    │
│   │  database-engineer  │      │                      │    │
│   │  data-model-engineer│      │                      │    │
│   │  backend-architect  │      │                      │    │
│   │  api-contract-eng.  │      │                      │    │
│   │  platform-engineer  │      │                      │    │
│   └─────────────────────┘      └──────────────────────┘    │
│              │                                             │
│   ┌──────────▼──────────┐      ┌──────────────────────┐    │
│   │      SKILLS (30)    │      │   PLUGINS (7)        │    │
│   │  process / ai-core  │      │  gates.ts            │    │
│   │  advanced / RE      │      │  memory.ts           │    │
│   │  human-voice /      │      │  voice-guard.ts      │    │
│   │  anti-delirium      │      │  verify-guard.ts     │    │
│   └─────────────────────┘      │  publish-guard.ts    │    │
│              │                  │  delegation-guard.ts │    │
│   ┌──────────▼────────────────┐ │  research-guard.ts   │    │
│   │      MCP SERVERS          │ └──────────────────────┘    │
│   │  filesystem · context7    │                             │
│   │  playwright · chrome-devtools│                          │
│   └───────────────────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Orchestrator (`agents/ai-orchestrator.md`)
Primary agent. The single interface with the user. Runs the
CAPTURE → DISCUSS → DEFINE → REWRITE → DELEGATE → SYNTHESIZE loop.
Carries deep AI engineering + SWE knowledge. Routes via `skills/ai-orchestration`.

### Subagents (13)
Each is a leaf specialist. Receives objective + context + output contract + boundaries
from the orchestrator. Reports findings; never acts alone.

| Domain | Agents |
|--------|--------|
| AI/LLM | deep-researcher, ai-architect, ai-evals-runner, llm-security-reviewer |
| Security | red-team-agent, bug-bounty-hunter, security-defensive |
| Database | database-engineer, data-model-engineer |
| Backend | backend-architect, api-contract-engineer |
| Platform | platform-engineer |
| Niche | reverse-engineer |

### Skills (30)
Methodology packages the model loads on demand. `ai-engineering-standards` is
transversal (all inherit it). `human-voice` and `anti-delirium` are the two disciplines
every agent follows. `ai-orchestration` is the routing protocol. Reverse engineering has
its own cluster (re-binary-analysis through re-firmware-analysis).

### Memory (`scripts/memory/foundry_memory.py`)
SQLite + FTS5 + optional semantic embeddings (fastembed/ONNX). Living loop:
- **Encode**: plugins capture errors→gotchas, commits→memories; agents feed findings/decisions
- **Consolidate**: dedup, confidence++, temporal decay
- **Retrieve**: recall injected into system prompt (`---foundry-memory---`)
- **Reconsolidate**: recall acted on reinforces; ignored decays

Privacy: 100% local, never versioned, blocks secret/PII patterns.

### Evals
Golden-sets + rubric + baseline. `scripts/eval-runner.py` runs 35 deterministic checks
(engine, routing, plugins, K=5 stability) in CI on every push. Regression gate before
anything ships.

## Data flow (one request)

1. User sends a request to the orchestrator.
2. Orchestrator loads memory recall (past findings, decisions).
3. If ambiguous → asks questions until it can write a SPEC.
4. Writes SPEC, gets approval, rewrites into delegation prompts.
5. Routes to subagents (parallel when independent).
6. Subagents feed findings back to memory.
7. Orchestrator synthesizes and presents options to the user.

## Invariants

- Subagents never act independently.
- Every delegation carries objective + context + output + boundaries.
- Every agent feeds the memory loop.
- Gates are mechanisms, not instructions.
- No model is called without a defined purpose (cost discipline).
- **Anti-delirium**: every factual claim has proof or a confidence marker. Never conjecture.
- **Human voice**: output never reads like AI-generated text.
- **Model routing**: reasoning → PRO, mechanical → FLASH (docs/MODEL-POLICY.md).
- **Mode routing**: ambiguity/stakes → PLAN first, clear/approved → BUILD.

## Plugins

| Plugin | Enforcement |
|--------|-------------|
| `gates.ts` | blocks commit without tests, secret staging, secret egress |
| `memory.ts` | captures + recall injection (the memory loop runtime) |
| `voice-guard.ts` | flags AI-tell text in file output (dashes, AI vocabulary) |
| `verify-guard.ts` | flags conjecture-as-grounding in file output (anti-delirium) |
| `publish-guard.ts` | injects mandatory human-voice + anti-delirium + standards gate into every system prompt |
| `delegation-guard.ts` | validates subagent spawns (4 mandatory parts + routing table check) |
| `research-guard.ts` | enforces research delegation: warns on direct webfetch, forces deep-researcher |
