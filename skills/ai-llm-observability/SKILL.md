---
name: ai-llm-observability
description: Observability for LLM applications, structured logging, tracing, token/cost tracking, and RED metrics. Use when instrumenting or debugging LLM apps and agents.
---

# AI LLM Observability

Instrument LLM apps so failures are diagnosable and costs are visible. Instrument as you
build, not after.

## What to capture per request

- **Request**: prompt (truncated), model, provider, params, tool calls
- **Response**: output (truncated), finish reason, latency
- **Usage**: input/output/cached tokens, cost estimate
- **Context**: session id, user id (hashed), conversation metadata
- **Outcome**: success / error / degraded / fallback used

## Structured logging

Log JSON lines with context, never bare strings.

```json
{"level":"info","service":"llm-gateway","event":"completion","model":"deepseek-v4-pro","input_tokens":1500,"output_tokens":420,"latency_ms":3100,"finish":"stop","error":null}
```

Log the failure AND the degradation path (fallback used), don't swallow it.

## Tracing

- Trace the full agent loop: tool call → result → decision, not just the LLM call.
- Propagate a trace/session ID across spans.
- OpenTelemetry for cross-service traces; structured logs for the LLM layer.
- Tag spans: model, tool, error, fallback.

## Cost tracking

- Compute cost per request from token counts × model price table.
- Aggregate per session, per feature, per model. Alert on spikes.
- Track cached reads separately (cheap), they dominate DeepSeek usage patterns.

## RED metrics

| Metric | Meaning |
|--------|---------|
| Rate | requests/sec per endpoint/model |
| Errors | error rate, by error class |
| Duration | latency p50/p95/p99 |

Plus: token rate, cost rate, fallback rate, timeout rate.

## Alerting (symptom-based)

- Alert on symptoms: error-rate spike, p95 latency breach, cost spike, fallback storm.
- Not on "model changed", that's a cause, not a symptom.

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| Log after prod breaks | Instrument at build time |
| Bare string logs | JSON lines with context |
| No usage/cost | Track tokens + cost per request |
| LLM-only tracing | Trace the agent loop + tools |
| Alert on causes | Alert on symptoms |

## Verification

- Every LLM call logs structured usage + cost
- Agent loop traceable end-to-end
- RED metrics computed and dashboarded
- Cost aggregated and alertable
- Fallback/degradation path observable
