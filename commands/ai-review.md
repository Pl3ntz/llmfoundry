---
description: Security review of an LLM app, agent, or RAG system before shipping
model: opencode/deepseek-v4-flash-free
agent: llm-security-reviewer
---

Security review using the `ai-llm-app-security` skill.

**Target:** {{argument}}

Run the full threat-model checklist:
1. Prompt injection (instruction/data boundary)
2. Data exfiltration (egress points, outbound scan)
3. SSRF via LLM tools (URL validation, allowlists)
4. Tool abuse / excessive agency (least privilege)
5. Abuse & cost control (rate limits, quotas)
6. Data exposure (secrets in context, retrieval grounding)

Output the FINDINGS/EXPOSURE/PASSED/NEXT STEP contract. Every finding with `file:line` + evidence.
