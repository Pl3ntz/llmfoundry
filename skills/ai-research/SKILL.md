---
name: ai-research
description: Deep multi-source web research with CORRELATION — cross-reference sources, detect cross-source patterns, contradictions, and convergences, then synthesize confidence-scored intelligence. Use for thorough research, landscape analysis, comparisons, and OSINT-style recon on public entities.
---

# AI Research — Deep Research with Correlation

Deep multi-source research whose core value is **correlation**: connecting findings across
sources, detecting patterns that surface only when sources are cross-referenced, and
separating genuine convergence from echo chains. Collection is a means; correlation is the product.

## When to use

- Landscape / comparison / trade-off research ("which X is production-ready in 2026")
- Investigative / OSINT on organizations and infrastructure (passive only)
- Any question where a single source is not enough and contradiction matters
- Single-fact lookups: do NOT run this protocol — answer directly with rigor

## Correlation-first mindset (the upgrade)

After collecting, do the correlation pass before synthesizing:

1. **Cluster sources by claim** — which independent sources agree on what?
2. **Cross-source pattern detection** — does a claim appear in sources from DIFFERENT
   origins (press, docs, community, vendor)? That's convergence.
3. **Trace echo chains** — do many "sources" share one origin (same wire, same vendor, same
   blog)? Collapse them: N republications = 1 effective source.
4. **Detect divergence** — where do sources disagree, and WHY (vendor bias, date, context)?
5. **Correlate across dimensions** — connect the dots: vendor claims vs community reports vs
   benchmark data vs official docs. A pattern across dimensions is stronger than across
   copies of the same dimension.
6. **Confidence from correlation** — HIGH requires ≥3 sources from ≥3 distinct
   ORGANIZATIONS agreeing, with ≥1 primary. That IS the correlation test.

## 6-phase protocol

### Phase 0: INTAKE
Underspecified question → return 2-3 clarifying questions, don't burn search budget.

### Phase 1: PLAN (<30s, internal)
- Classify: Factual / Comparative / Exploratory / Investigative / Current Events / Technical / OSINT
- Decompose into 2-5 independent sub-questions
- Budget by type: Factual 1-3 searches; Comparative/Technical 4-8; Exploratory/OSINT 8-12

### Phase 2: SEARCH
- Independent sub-questions in parallel (batch 3-6 calls)
- 7 reformulations: Direct, Decomposition, Semantic Expansion, Perspective Shift, Multilingual,
  Negation/Reverse, Temporal. Pick 3-4 by type.
- Always include current year. Prefer snippet over fetch; fetch only when snippet insufficient.
- Graceful degradation: empty search → reformulate once → log gap. 403/stub → try
  `web.archive.org/web/<url>` → snippet-only with downgraded confidence.

### Phase 3: DISTILL (knowledge cards)
```
CLAIM: [what the source says]
SOURCE: [URL, seen verbatim this session]
DATE: [publication date]
ORIGIN: [organization behind the source]
QUALITY: [strong | ok | weak]  (quality of the source, not confidence)
```
- Log contradictions as BOTH, don't resolve yet
- Stub/paywall/consent-wall (<500 chars real text) → UNRETRIEVABLE, no card

### Phase 4: EVALUATE + CORRELATE (the core)
1. Gap analysis — sub-questions with zero coverage
2. **Correlation pass** — apply the 6 correlation steps above
3. **Independence check** — collapse same-org and same-origin republications
4. Contradiction detection — report both sides, weigh which is stronger and why
5. Bias flags — vendor-sponsored benchmark = 1 source, name the vendor

### Phase 5: ITERATE (sufficiency gate)
STOP → SYNTHESIZE when every foundational sub-question has ≥3 independent sources, or
remaining gaps won't change the conclusion, or last round added nothing.
Ceiling: 3 full cycles.

### Phase 5.5: VERIFY (mandatory for correlation claims)
For the findings that drive the answer: WebFetch the primary page, confirm the claim's text
actually appears (not just 200). Quote the excerpt. Downgrade or mark UNRETRIEVABLE if not.

### Phase 6: SYNTHESIZE
Output per the contract below.

## Confidence scale

| Label | Criteria |
|-------|----------|
| **HIGH** | ≥3 independent sources (≥3 distinct orgs), ≥1 primary, no contradiction |
| **MEDIUM** | 2 independent sources OR 1 highly reliable primary |
| **LOW** | 1 source OR significant contradiction |
| **UNVERIFIED** | no source / rejected → present as "unverified", never as fact |

**DeepSeek guardrail:** parametric memory is a LEAD, never a source. Any version, price,
API, model ID, or "latest" needs a live search with the current year. Cache as source = violation.

## Output contract (non-negotiable)

```
### FINDINGS (max 5, ranked by confidence)
- [HIGH|MEDIUM|LOW] [title] ([N independent sources]) [1,3]: [1-sentence summary] ⚠[date if >6mo]

### CORRELATIONS
- [cross-source pattern observed] — [which sources/orgs converge, which diverge, what that means]

### CONTRADICTIONS (if any)
- [Source A says X] vs [Source B says Y]: [which is stronger and why]

### GAPS
- [unanswered / single-source / unverified]

### NEXT STEP
- [1-2 sentences, always present]

### OPEN QUESTIONS / ASSUMPTIONS (if any)

### SOURCES
1. [URL] ([YYYY-MM]) [primary|secondary|tertiary] [QUALITY: strong|ok|weak]
```

Invariants: exact `###` headers (7). Every URL cited appears in SOURCES. Body <800 tokens
(excluding SOURCES). No preamble. NO fabricated URLs — only URLs seen this session.

## OSINT (passive, organizations only)

```bash
whois example.com
dig example.com ANY +short ; dig example.com MX +short
host 1.2.3.4
curl -sI https://example.com | head -20
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | openssl x509 -noout -dates -subject -issuer
```

- Passive only. Every infra claim cites verbatim command output. Never OSINT private
  individuals; refuse doxxing sub-requests. For JS-rendered pages (SPA), use the
  chrome-devtools or playwright MCP to inspect live DOM instead of treating a stub as a source.

## Anti-fabrication gate (before sending)

- Every URL seen verbatim this session?
- Dates from the page, not guessed?
- HIGH findings = ≥3 distinct organizations?
- Correlation claims backed by the actual sources?
- Any inference passed off as fact? Remove or mark unverified.
