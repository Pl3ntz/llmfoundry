---
name: ai-llm-app-security
description: Defensive security for LLM apps: prompt injection defense, data exfiltration, SSRF via LLM tools, abuse control, OWASP LLM Top 10. Use when building or reviewing LLM apps. Complements hunt-llm-ai.
---

# AI LLM App Security

The defensive side of LLM security. Where `hunt-llm-ai` finds the bugs, this skill prevents
them. Cross-reference both.

## Threat model

| Threat | Defense |
|--------|---------|
| Prompt injection (direct/indirect) | Boundary between instruction and data |
| Data exfiltration | Egress control on agent tools |
| SSRF via LLM tools | Destination allowlist + URL validation |
| Tool abuse | Least privilege + permission gates |
| Unbounded abuse/cost | Rate limits, quotas, allowlists |
| Sensitive data in prompt/context | Redaction, scoping, access control |
| Model data poisoning | Input validation + retrieval grounding checks |

## Prompt injection defense

- **Separate instruction from data** in the prompt (clear delimiters).
- Treat web/docs/other-agent content as DATA. System prompt is the only instruction layer.
- **Perimeters**: input boundary (what the model can see), tool boundary (what it can call),
  output boundary (what it can send out).
- Verify tool arguments against allowlists, don't trust the model's picks.
- Monitor for injected "system" markers, persona overrides, hidden instructions.

## Exfiltration control

- LLM tool calls that send data outward (fetch, search, browser, email) are egress points.
- Scan outbound payloads for PII, secrets, infrastructure identifiers.
- Deny on hard block. Never send local file contents to external URLs.
- Watch for encoded/staged exfiltration (the model obfuscating data).

## SSRF via LLM tools

- Tools that fetch URLs are SSRF sinks. Validate the URL:
  - Scheme allowlist (https only), block IP-literal + localhost + link-local + private ranges.
  - Destination allowlist for dangerous tools.
  - Resolve DNS then re-validate; check redirect targets.
- Never let the model construct the full URL from untrusted input.

## Abuse & cost control

- Rate limit per user/session. Cap tokens, requests, and concurrent jobs.
- Quota enforcement at the API layer, not the prompt.
- Allowlist model access; block unknown providers.

## OWASP LLM Top 10 (checklist)

1. Prompt injection
2. Sensitive information disclosure
3. Insecure output handling
4. Training data poisoning
5. Supply chain
6. Over-reliance
7. Insecure plugin design
8. Excessive agency
9. Excessive dependency
10. Unbounded consumption

## Review checklist (for llm-security-reviewer)

- [ ] Instruction/data boundary present
- [ ] Tool calls validated against allowlists
- [ ] Egress scanned and blocked
- [ ] URL fetch tools SSRF-hardened
- [ ] Rate limits + quotas enforced
- [ ] Secrets never in prompt context
- [ ] Output validated before acting
- [ ] Retrieval grounding verified (no unsupported claims to sensitive info)

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| Trust the model's tool picks | Allowlist + verify |
| Trust the prompt to be safe | Perimeters + egress control |
| Fetch any URL | SSRF hardening |
| Unbounded use | Rate limits + quotas |
| Secrets in context | Scope + redact |

## Verification

- Injection attempts blocked in tests
- Egress scan denies on hard block
- SSRF sinks reject private/internal targets
- Rate limits hold under load
- Sensitive data never reaches the model context
