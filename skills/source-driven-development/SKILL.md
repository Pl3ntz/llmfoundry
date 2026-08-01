---
name: source-driven-development
description: Ground every framework, library, and API decision in official documentation. Verify versions, cite sources, flag what's unverified. Use when using any framework/library/API where the model's memory may be stale or wrong.
---

# Source-Driven Development

Ground every technical decision in official, verifiable sources. DeepSeek's parametric
memory of APIs and versions is stale — never trust it for specifics.

## When to use

- Using a framework, library, SDK, or API
- Any version, model ID, function signature, or parameter matters
- Writing code that must compile/run on the first try

## Process

### 1. Identify the source of truth
For any dependency: the official docs, the official repo, the package registry, the
official release notes. Not a blog, not AI output, not memory.

| Need | Source of truth |
|------|-----------------|
| Current version | npm/pypi/crates registry, release notes |
| API signature | official docs / type definitions / source |
| Behavior | official docs, changelog, tests in the official repo |
| Deprecations | official changelog / migration guide |

### 2. Verify before you write
- Confirm the version exists in the registry
- Confirm the exact API surface (function name, params, return) from official types/docs
- Confirm the import path and setup
- Use `context7` MCP or fetch the official docs page

### 3. Write, then re-verify
- After writing, check each dependency usage against the source again
- Flag anything you could NOT verify as unverified rather than guessing

### 4. Cite your ground
- For non-trivial choices, note where you verified: `per docs: https://...`
- Distinguish: verified-in-docs / unverified (mark clearly)

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| "The API is X" from memory | Verify in docs/types |
| "Latest is X" | Check the registry |
| Copy-paste example without checking version | Confirm it applies to your version |
| Assume deprecation status | Check changelog/migration guide |
| Unverified but confident | Mark unverified, then verify |

## Verification

- Every dependency's version confirmed in its registry
- Every API call matches official types/docs
- Nothing cited from memory that could be stale
- Unverified items flagged, not hidden
