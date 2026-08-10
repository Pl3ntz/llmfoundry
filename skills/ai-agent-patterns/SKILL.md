---
name: ai-agent-patterns
description: Architecture patterns for AI agents: tool-use loops, context management, subagents, agentic workflows, failure handling. Use when designing or building agentic systems.
---

# AI Agent Patterns

Architecture patterns for building agents that reliably use tools, manage context, and
complete multi-step tasks.

## Core loop

```
USER TASK
  → plan (route + decompose)
  → tool call
  → observe result
  → decide: done or next step
  → bounded loop (max iterations)
  → verify + report
```

Every agent needs: a loop bound, a stop condition, and a failure path.

## Tool-use patterns

- **Describe tools precisely** (see `ai-prompt-engineering`). Vague descriptions = wrong calls.
- **Single tool per step** for dependent steps; parallel tool calls for independent ones.
- **Handle tool failures explicitly**: retry with backoff for transient, alternative tool
  for permanent, surface for unexpected.
- **Never let the agent guess tool output.** It must read/observe the real result.

## Context management

- Give the agent only what it needs (see `ai-context-engineering`).
- Streaming/scratchpad for long tasks, don't accumulate everything in context.
- Summarize intermediate results, keep the goal and constraints in context.
- Know the context budget and stay under it.

## Subagent patterns

| Pattern | Use when |
|---------|----------|
| Fan-out | Independent subtasks in parallel (research, reviews) |
| Pipeline | Sequential stages with handoff (spec → build → review) |
| Recursive | Decompose until leaf tasks, then unwind |
| Supervisor | Orchestrator delegates, synthesizes, never does leaf work |

Subagents get: objective, output format, boundaries. Never spawn without a clear contract
and a defined way to verify the result.

## Agentic workflow anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| Infinite loop | Hard iteration cap |
| Tool spamming | Budget per step, single intent per call |
| Context bloat | Summarize intermediate, prune |
| Over-planning | Act after the first lightweight plan |
| No verification | Every workflow ends with a verification step |

## Failure handling

1. Classify: transient / permanent / context / tool-misuse
2. Transient → retry with backoff (1s, 2s, 4s)
3. Permanent → alternative path or surface to user
4. Tool misuse → tighten description, add guard
5. Unrecoverable → fail loudly with what was tried

## Verification

- Loop terminates under all inputs
- Every tool result is observed, not guessed
- Output meets the contract (format + evidence)
- Failure paths tested: tool errors, empty results, malformed input
