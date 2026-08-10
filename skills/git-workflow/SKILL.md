---
name: git-workflow
description: Professional git practices: trunk-based development, atomic commits, branching, safe merging. Use when committing, branching, resolving conflicts, or reviewing history.
---

# Git Workflow

Git is your safety net. Commits are save points, branches are sandboxes, history is
documentation. With agents generating code fast, disciplined git is what keeps changes
reviewable and reversible.

## Trunk-based development (recommended)

Keep `main` always deployable. Work in short-lived feature branches merged within 1-3 days.
Long-lived branches diverge, conflict, and delay integration. DORA research correlates
trunk-based development with high-performing teams.

```
main ──●──●──●──●──●──●──  (always deployable)
        ╲      ╱  ╲    ╱
         ●──●─╱    ●──╱   ← short-lived branches (1-3 days)
```

- **Dev branches are costs.** Every day alive adds merge risk.
- **Release branches are acceptable** when stabilizing a release while main moves.
- **Feature flags over long branches.** Deploy incomplete work behind flags instead of
  holding it on a branch for weeks.

## Commit early, commit often

Each successful increment gets its own commit. Never accumulate a giant uncommitted blob.

```
Good:   Implement slice → Test → Verify → Commit → Next slice
Bad:    Implement everything → Hope it works → Giant commit
```

Commits are save points. If the next change breaks something, revert to the last known-good.

## Atomic commits

One commit, one logical thing.

```
# Good: self-contained commits
a1b2c3d Add task creation endpoint with validation
d4e5f6g Add task creation form component
h7i8j9k Connect form to API, add loading state

# Bad: everything mixed
a1b2c3d WIP big feature
```

Rules:
- Commit a feature slice that leaves the tree in a working state.
- Never commit red tests or a broken build.
- Message answers "why", not just "what". Body explains the reason when non-obvious.

## Conventional commit messages

```
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.
Scope is optional (the module). Example: `feat(auth): add token refresh`.

- Imperative mood: "add", "fix", "remove". Not "added", "fixed".
- Lowercase start. No trailing period. No emoji. No attribution trailers.
- This repo's gates enforce conventional messages on commit.

## Branching

- Feature branches: `feat/<short-name>`.
- Fix branches: `fix/<short-name>`.
- Keep them short-lived and rebased on main before merge.
- Prefer `git worktree add` for parallel work (physical isolation beats discipline).

## Merging and resolving conflicts

- **Rebase feature branches on main** before merging to keep history linear and
  conflicts small.
- Conflicts: resolve manually, test after, never force-resolve blindly.
- For a PR, diff the whole branch: `git diff <base>...HEAD`, not just the last commit.
- After merge, delete the branch. A dead branch is a cost.

## Git hygiene anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| Giant WIP commits | Atomic commits per increment |
| Commit broken build | Only commit green trees |
| Long-lived branch | Merge within 1-3 days |
| `git add -A` blindly | Stage explicit files (see gates env-guard) |
| Rewrite pushed history casually | Only with explicit force policy |
| Commit secrets | Blocked by gates; double-check staged files |

## Verification

- `main` stays deployable
- Every commit is atomic and green
- Feature branches short-lived
- History readable (conventional messages)
- Staged content reviewed before commit (gates enforce)
