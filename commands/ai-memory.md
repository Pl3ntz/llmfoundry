---
description: Interact with the local memory, remember, search, recall, promote, stats
model: opencode-go/deepseek-v4-flash
agent: build
---

Use the foundry-memory CLI to interact with local memory.

**Action + argument:** {{argument}}

The memory CLI is at `scripts/memory/foundry_memory.py`. Commands:

- `remember <content> [--container C] [--type T]`, store a structured memory
- `fact <container> <static|dynamic|gotcha> <text>`, store/reinforce a profile fact
- `gotcha <container> <pattern> [--category C] [--sample S]`, record a recurring error
- `finding <container> <agent> <text> [--severity S]`, record an agent finding
- `search <query> [--container C]`, full-text search
- `recall [--container C] [--top N]`, recall open findings + gotchas
- `promote --container C`, promote recurring gotchas to curated layer
- `stats [--container C]`, memory stats
- `decay`, apply temporal decay

Interpret the request:
- "lembra/anota X" → `remember`
- "o que sabemos sobre X" → `search`
- "o que lembra?" → `recall`
- "stats/estatisticas" → `stats`
- "promove gotchas" → `promote`

Run the appropriate command via bash and report the output. Memory is local-only.
