---
description: Deep multi-source research with correlation and confidence scoring
model: opencode/deepseek-v4-flash-free
agent: deep-researcher
---

Deep research using the `ai-research` skill (correlation-first protocol).

**Research question:** {{argument}}

Run the 6-phase protocol: INTAKE → PLAN → SEARCH → DISTILL → EVALUATE+CORRELATE → ITERATE → SYNTHESIZE.

Focus on CORRELATION: cluster sources by claim, trace echo chains, detect cross-source
patterns and divergence, weight contradictions. Confidence from correlation: HIGH = 3+
distinct organizations, 1+ primary.

Output the exact contract: FINDINGS, CORRELATIONS, CONTRADICTIONS, GAPS, NEXT STEP,
OPEN QUESTIONS, SOURCES. No fabricated URLs. Body <800 tokens excluding SOURCES.
