---
name: ai-prompt-engineering
description: Design, iterate, and evaluate system prompts, few-shot examples, tool descriptions, and structured output. Use when writing or improving prompts for LLM apps, agents, or evals.
---

# AI Prompt Engineering

Disciplined process for writing and iterating prompts that behave reliably, especially on
DeepSeek-family models with lower guardrails.

## Prompt anatomy

```
SYSTEM  → who the model is, rules, boundaries, tone
CONTEXT → what the model needs to know (data, constraints)
TASK    → what to do, output format
FORMAT  → schema, JSON shape, exact headers
```

Write these separately, don't mush them together.

## Rules for DeepSeek models

1. **Explicit output contract.** JSON schema or exact headers, not "respond nicely". If the
   output must parse, give the schema and demand valid JSON.
2. **State rules as commands, not suggestions.** "Return only the JSON object." Not "you
   should consider returning JSON."
3. **Few-shot beats description.** One correct example beats three sentences describing what
   you want. Include the failure mode too: an example of what NOT to output.
4. **Constrain tools.** Every tool description = purpose + when to use + what it returns.
   Vague descriptions get called at the wrong time.
5. **Anchor, don't assume.** DeepSeek parametric memory is stale. Say "answer only from the
   provided context" when grounding matters.
6. **Guardrails in the prompt** (model has fewer): input boundary, refusal policy, output
   boundary. Compensate explicitly.

## Iteration loop

1. Write prompt + test cases (golden set)
2. Run against a fixed input
3. Diagnose failures: over-generation? wrong format? hallucination? refusals?
4. Fix ONE thing per iteration. Re-test the SAME cases
5. Track a prompt version — change prompts through the `ai-evals` flow, not ad hoc

## Structured output patterns

```json
{ "type": "json_schema", "schema": { "name": "result", "strict": true, "schema": { "type": "object", "properties": { "answer": { "type": "string" }, "confidence": { "type": "number" } }, "required": ["answer", "confidence"], "additionalProperties": false } } }
```

If the provider supports structured output, use it — never parse prose.

## Tool description template

```
## search_docs
- Purpose: Find the latest documentation for a library
- When: user asks about an API or version; never use for general questions
- Returns: list of {title, url, snippet}
```

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| "Be helpful and accurate" | Specific rules + format contract |
| No example | Add few-shot with success + failure |
| Long boilerplate | Cut to what changes behavior |
| Prompt as prose | Structure: SYSTEM/CONTEXT/TASK/FORMAT |
| "Think step by step" without output bounds | Bound the reasoning, demand the format |

## Verification

- Does the golden set pass? (see `ai-evals`)
- Does the output parse under the schema?
- Does the model refuse or hedge on edge cases?
- Did any example get followed exactly?
