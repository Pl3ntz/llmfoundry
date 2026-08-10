---
name: pull-request
description: "Create effective pull requests: small reviewable diffs, clear descriptions, healthy review loops. Use when opening or updating a PR, responding to review, or preparing a change for merge."
---

# Pull Request

A PR is the unit of reviewable work. Its quality determines review speed, merge safety,
and how well the team understands the change. A good PR makes review fast and merge easy.

## Change sizing (the single biggest factor)

**Small PRs review faster and merge cleaner.** The rule: around 100 lines or less per PR.

| Size | Review reality |
|------|----------------|
| < 100 lines | Fast, thorough review, quick merge |
| 100-300 lines | Reviewable with focus |
| 300-1000 lines | Review fatigue, missed issues |
| > 1000 lines | Rarely reviewed properly, high merge risk |

If a change is large, split it into logical PRs that each merge independently:
- Extract the refactor first, then the feature.
- Keep each PR independently shippable (don't break main between PRs).

## Before opening a PR

1. **Branch is rebased on main** and conflict-free.
2. **Tests pass, lint clean, build green.** No red CI.
3. **Diff reviewed by yourself first** (`git diff <base>...HEAD`) for obvious issues.
4. **No secrets, no debug leftovers, no unrelated changes.** The diff touches only what
   the PR claims.
5. **Structure sync (MANDATORY).** If the PR adds, removes, or changes agents, skills,
   commands, plugins, or MCPs, it MUST also update: SKILLS.md, README.md (counts + tables),
   agents/ai-orchestrator.md (routing), skills/ai-orchestration/SKILL.md (routing), and
   any docs naming the structure. The orchestrator can only route to what it knows, so a
   structural change without the routing tables updated is an incomplete PR. State in the
   PR description what was synced.

## The PR description

A reviewer should understand the change without reading all the code. Write:

```
## What
[what this PR does, in 1-3 sentences]

## Why
[the problem it solves, the context]

## Changes
- [bullet list of the meaningful changes]

## Testing
- [what was tested, how to reproduce, commands run]

## Screenshots (if UI)
[before/after where useful]

## Notes
[anything unusual, follow-ups, trade-offs]
```

Rules:
- Write it yourself with human voice (see human-voice). No template-y filler.
- Concrete "Testing" section beats "tested locally". Give commands.
- Reference the issue it closes: "Closes #42".

## The review loop

- **Author's job:** respond to every review comment, fix or explain. Never dismiss
  silently. Keep the loop tight: address feedback, push, re-request review.
- **One change per push** keeps the diff reviewable. Batch related fixes.
- **Update the description** if the change evolves meaningfully.
- When review asks for changes, make them, don't argue the point into the ground. If a
  comment is wrong, explain briefly and move on.

## Draft PRs

- Open as **Draft** until it's ready for review. Reviewers shouldn't review half-finished
  work.
- Mark ready when: code complete, tests pass, description written.

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| 2000-line PR | Split into shippable chunks |
| Empty description | What, why, changes, testing |
| No testing section | Concrete commands the reviewer can run |
| Ignore review comments | Respond to every one |
| Merge with red CI | Gate: CI must be green |
| Include unrelated changes | Keep the diff focused |

## Verification

- PR ≤ ~100 lines when possible
- Description has what, why, testing
- CI green before merge
- Every review comment addressed
- Merge deletes the branch
