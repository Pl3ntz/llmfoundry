---
name: ai-dev-process
description: Mandatory development process for AI engineering work: SPEC, TDD, git worktree, atomic commit. Use before writing any code.
---

# AI Dev Process

Mandatory workflow for every task that writes code. Do not skip steps.

## The flow

```
1. SPEC       → objective, scope, out-of-scope, done criteria → approval
2. WORKTREE   → git worktree add for the feature
3. TDD        → tests first (red) → implement (green) → refactor
4. VERIFY     → typecheck + lint + full test suite
5. COMMIT     → atomic commit, conventional message (see git-workflow)
6. REVIEW     → self-review + code-review on the diff (see code-review)
7. PR         → small, described, CI green (see pull-request)
8. MERGE      → merge worktree back
```

For git practices, PR creation, and effective review, load `git-workflow`,
`pull-request`, and `code-review` respectively. They are part of this process.

## 1. SPEC first

For anything beyond a trivial edit, write a spec before code:

```markdown
### SPEC: [title]
- **What**: [precise description]
- **Why**: [problem solved]
- **Scope**: [files/areas affected]
- **Out of scope**: [what is NOT done]
- **Done criteria**: [how to verify completion]
```

Wait for approval before implementing. Ambiguous? Ask 3-5 questions first (see `interview-me`).

## 2. Git worktree

Isolate every feature in its own worktree. Parallel work is a filesystem fact, not a promise.

```bash
git worktree add ../llmfoundry-feature -b feat/feature-name
cd ../llmfoundry-feature
```

Never edit the main working tree while a feature is in progress.

## 3. TDD

- Tests FIRST. Red → green → refactor.
- Minimum 80% coverage (unit + integration + E2E).
- Test the behavior, not the implementation.
- If it can't be tested, it's not done.

## 4. Verify

Before commit, run:
```bash
# typecheck + lint + tests
npm run typecheck && npm run lint && npm test
# or your stack's equivalent
```

No red commits. No commit that skips verification.

## 5. Atomic commit

- One commit = one logical unit. Never mix feature + fix + refactor.
- Conventional message: `feat:|fix:|refactor:|test:|docs:|chore:|perf:|ci:`
- Small, reviewable diffs (~100 lines or less).
- No attribution trailers, no emoji, no "Generated with".

## 6. Merge

```bash
git checkout main
git merge feat/feature-name
git worktree remove ../llmfoundry-feature
```

## Rationalization check

| Excuse | Rebuttal |
|--------|----------|
| "I'll write the spec after" | No. Spec first or it's not spec'd, it's a guess |
| "Tests would take too long" | Tests are the definition of done. No tests = not done |
| "It's a small change, skip worktree" | Small changes break too. Isolate anyway |
| "I'll commit and fix in next commit" | One atomic commit or it didn't happen cleanly |
