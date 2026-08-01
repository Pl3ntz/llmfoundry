---
name: debugging-and-error-recovery
description: Systematic 5-step debugging, reproduce, localize, reduce, fix, guard. Use when tests fail, builds break, behavior is unexpected, or a production issue arises.
---

# Debugging and Error Recovery

Five-step triage. Stop-the-line rule: when something breaks, fix the root cause before
moving on, don't paper over it.

## The 5 steps

### 1. REPRODUCE
- Reproduce the failure deterministically. "It failed once" is not a bug you understand.
- Capture the exact input, state, and error. Write a failing test that reproduces it.
- If you can't reproduce, collect evidence: logs, stack traces, timing, conditions.

### 2. LOCALIZE
- Find the smallest scope: which function, which call, which condition.
- Bisect: binary search the code/data/commits to isolate the change that broke it.
- Read the actual code path, don't reason from the symptom.
- Check the boundary: is it the input, the code, or the environment?

### 3. REDUCE
- Reduce the failure to its minimal form: smallest input, fewest moving parts.
- A minimal reproduction is the test you'll keep.
- Remove variables: is it data-dependent? concurrency? timing? config?

### 4. FIX
- Fix the root cause, not the symptom.
- Write the test that failed first (red), then fix (green).
- Fix ONE thing. Re-run the full suite after.
- No drive-by changes while debugging.

### 5. GUARD
- Add the regression test that would have caught it.
- Consider: input validation, boundary checks, error handling, alerting.
- Ask "why didn't this fail loudly?" and fix that too.

## Stop-the-line rule

When a test fails or the build breaks, STOP the current task and fix it before continuing.
Deferred "I'll fix it later" becomes a recurring cost.

## Error taxonomy

| Error type | Approach |
|------------|----------|
| Build/type error | Fix at the source, don't suppress |
| Test failure | Reproduce → was it the code or the test? |
| Runtime crash | Reproduce with the exact input, fix root cause |
| Flaky/timing | Find the race, often shared state or timing assumption |
| Environment | Check versions, config, env vars before code |
| Production issue | Reproduce from logs, reduce, fix, guard with alerting |

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| "It worked before" | Bisect to find what changed |
| Fix the symptom | Fix the root cause + add the test |
| Debug by print spamming | Reproduce + localize systematically |
| Skip the regression test | Guard step is mandatory |
| "Probably fixed" | Re-run the full suite, prove it |

## Verification

- Failure reproduces deterministically (or evidence collected)
- Root cause identified, not just symptom
- Failing test added, passes after fix
- Full suite green
- Regression guard in place
