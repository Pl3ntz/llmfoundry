---
description: Write a SPEC before starting work, objective, scope, out-of-scope, done criteria
model: opencode/deepseek-v4-flash-free
agent: build
---

Write a SPEC for the following request using the `ai-dev-process` and `interview-me` skills.
If the request is ambiguous, ask 3-5 clarifying questions FIRST.

**Request:** {{argument}}

Output the SPEC in this exact format:

```
### SPEC: [title]
- **What**: [precise description]
- **Why**: [problem solved]
- **Scope**: [files/areas affected]
- **Out of scope**: [what is NOT done]
- **Done criteria**: [how to verify completion]
- **Complexity**: Trivial | Medium | Complex
```

Wait for approval before implementing.
