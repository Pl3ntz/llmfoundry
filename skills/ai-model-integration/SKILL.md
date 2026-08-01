---
name: ai-model-integration
description: Integrate LLM providers (OpenAI, Anthropic, Google, DeepSeek, OpenAI-compatible), SDKs, streaming, structured output, retries, and fallbacks. Use when wiring models into an app.
---

# AI Model Integration

Wire LLM providers into applications with streaming, structured output, retries, and
graceful fallback.

## Provider selection

- **DeepSeek native** (V4 Pro/Flash): cheapest, 1M context, thinking mode, tool calls,
  JSON output. Base URL `https://api.deepseek.com` (OpenAI-compatible).
- **OpenAI-compatible** (DeepSeek, OpenRouter, local): `@ai-sdk/openai-compatible`.
- **Anthropic**: `@ai-sdk/anthropic`, Messages API, `tool_use` blocks.
- **Google**: `@ai-sdk/google`, Gemini format.
- Rule: match the SDK to the endpoint's real format. OpenAI-compatible providers with a
  `/v1/responses` endpoint need `@ai-sdk/openai`, not `openai-compatible`.

## Config

- API keys from env, never committed. `.env` gitignored.
- Base URL configurable (proxy, local models).
- Timeout per request (e.g., 300s), overridable.
- Model + provider as config, not hardcoded.

## Streaming

- Stream tokens to UI; buffer nothing beyond the current chunk.
- Handle stream errors mid-flight: retry, partial output, or surface.
- Backpressure: don't buffer unbounded.

## Structured output

- Use provider native structured output (JSON schema) when available.
- If not, post-validate with Pydantic/Zod and re-prompt once on failure.
- Never trust free-form text where a schema is required.

## Retries & fallback

- Transient errors (429, 5xx, timeout): retry with exponential backoff (1s, 2s, 4s), jitter.
- Model fallback chain: primary → secondary → degraded mode.
- Degraded mode: deterministic fallback (heuristic/cached result), not a 500.
- Rate limits: respect Retry-After; queue or degrade.

## Error taxonomy

| Error | Handle |
|-------|--------|
| 401/403 | config/auth, surface clearly |
| 429 | backoff, fallback model |
| 5xx | retry, fallback |
| timeout | retry, then degraded |
| malformed output | re-prompt once, then degraded |

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| Key in code | Env + gitignore |
| No timeout | Per-request timeout |
| Blocking on flaky upstream | Retry + fallback + degraded mode |
| Parse prose as data | Structured output + schema validation |
| No fallback | Critical path never depends on one flaky model |

## Verification

- Structured output parses under the schema
- Streaming works, mid-flight errors handled
- Retry/fallback tested (simulate 429/5xx)
- Keys only in env
