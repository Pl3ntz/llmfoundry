---
name: code-review
description: Extremely effective code review: five-axis review, severity labels, evidence discipline, actionable feedback. Use before merging any change.
---

# Code Review

A review is the last line of defense before code ships. Its job: catch what tests and CI
miss, and improve the code while it is cheap to change. Review the code, not the author.

## When to review

- Before every merge, no exceptions.
- Review uncommitted work (local) and PRs (remote).
- Review your own diff before opening a PR (self-review catches the obvious).

## The five-axis method

Review along five axes, in priority order. Don't just scan for bugs.

1. **Correctness** (highest): does this do what it claims? Edge cases, error paths,
   boundary conditions, concurrency.
2. **Security**: injection, secrets, auth, data exposure, unsafe deserialization. For LLM
   apps, add prompt injection and exfiltration (see ai-llm-app-security).
3. **Clarity**: can the next reader understand this? Naming, structure, complexity.
4. **Maintainability**: will this be easy to change? Duplication, coupling, dead code,
   test coverage.
5. **Performance**: only where it matters. N+1, unbounded loops, blocking I/O in async.

## Severity labels (be honest, don't inflate)

| Label | Meaning | Blocks merge? |
|-------|---------|---------------|
| **Critical** | security hole, data loss, broken contract | Yes, must fix |
| **High** | clear bug, missing error handling, broken path | Yes, should fix |
| **Medium** | quality, maintainability, weak edge case | Prefer fix, can follow up |
| **Low** | style, naming, minor | Optional, batch |

**Anti-delirium applies:** every finding must point to evidence (`file:line`) you actually
read. Never flag "could be vulnerable" without proving the exposure. Never guess behavior.

## How to review efficiently (the effective method)

1. **Read the diff first** with fresh eyes. What does it claim to do? What breaks?
2. **Read the surrounding context** for the files touched. A diff without context misses
   contract breaks.
3. **Run it mentally**: trace the main path and the error path. What happens with empty
   input, wrong type, concurrent access?
4. **Check the tests**: do they cover the new behavior? Are edge cases tested, or only the
   happy path?
5. **Write findings** with severity + evidence + a concrete fix.

## Feedback that authors can act on

- **Specific**: point to the line, describe the problem, suggest the fix.
- **Kind but direct**: "this could fail when X is empty because Y. Add a guard." Not
  "this is wrong".
- **Explain why**: the reason matters more than the correction.
- **Batch trivia**: collect Low items, don't pepper the author with 20 nits.

```
❌ "This is bad code."
✅ "Line 42: this query has no LIMIT, so it loads the whole table. Add `.limit(100)`
    to bound it, matches the pattern in listActiveCvs."
```

## Review your own code first

Before opening a PR, review your own diff with the same five-axis standard. Self-review
catches the obvious and makes the human review about the real issues.

## What a good review catches that CI misses

- Logic that is correct for the happy path but wrong on the edge
- Security holes tests don't exercise
- Design problems: the feature in the wrong layer, the wrong abstraction
- Missing test coverage for the behavior that matters

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| Review only the diff, no context | Read surrounding code |
| Only happy-path thinking | Trace edge + error paths |
| Vague "this is wrong" | Specific finding + evidence + fix |
| Nit-storm on Low items | Batch trivia, focus on substance |
| Rubber-stamp "LGTM" | Apply the five axes before approving |
| Review the person, not the code | Feedback targets the code, never the author |

## Verification

- Every merge passes a five-axis review
- Findings carry severity + `file:line` + concrete fix
- No critical/high issues left open at merge
- Reviewer read the code, not just skimmed the diff
- Feedback is actionable (author knows exactly what to do)
