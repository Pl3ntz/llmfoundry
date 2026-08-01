---
description: Build with the mandatory process — SPEC, worktree, TDD, verify, atomic commit
model: opencode-go/deepseek-v4-pro
agent: build
---

Execute the build using `ai-dev-process` and `ai-engineering-standards` skills.

**Task:** {{argument}}

Follow the flow exactly:
1. SPEC first — write it, get approval
2. `git worktree add` for the feature
3. Tests FIRST (red) → implement (green) → refactor
4. Verify: typecheck + lint + full test suite
5. Atomic commit with conventional message
6. Merge worktree back

Do not skip any step. No red commits.
