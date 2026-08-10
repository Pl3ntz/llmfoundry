---
name: ai-context-engineering
description: Manage LLM context windows: packing, pruning, compaction, summarization, context budgets. Use when building prompts, agents, or any app with a context limit.
---

# AI Context Engineering

Feed models the right information at the right time, within the context budget.

## Context budget discipline

1. Know the model's context window (DeepSeek V4: 1M tokens) and the OUTPUT limit.
2. Reserve: system + task (~10%), tool results, conversation. Keep the working set small.
3. Over budget → quality drops, cost rises, failures increase. Prune before you exceed.

## Packing patterns

- **Progressive disclosure**, put the 100-token summary in context; load details on demand.
- **Recency weighting**, recent + goal + constraints always in context; history can be summarized.
- **Retrieval-in-context**, pull relevant chunks (see `ai-rag-pipeline`), don't dump everything.
- **Structured packing**, headers, delimiters, one topic per block. Models navigate structure.

## Pruning

Remove before you summarize:
- Tool outputs already consumed
- Repeated error messages
- Code blocks superseded by newer versions
- Anything not needed for the current step

## Compaction

When history exceeds the budget:
1. Summarize the conversation in structured form: decisions, done items, open items, constraints.
2. Keep the summary + last N messages + system prompt + current goal.
3. Never let compaction drop the goal or the acceptance criteria.

## Summarization contract

A good summary answers:
- What was the task? What is done?
- What decisions were made and why?
- What is open / blocked?
- What constraints are still active?

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| Dump everything | Pack by relevance, progressive disclosure |
| Never prune | Summarize consumed tool output |
| Compaction drops the goal | Goal + constraints are non-prunable |
| Full history in context | Roll up history, keep working set |
| Ignore the budget | Track tokens, stay under |

## Verification

- Total context stays under budget for the full run
- The model still knows the goal at the end (test it)
- No duplicate tool output in context
- Compaction preserved decisions and constraints
