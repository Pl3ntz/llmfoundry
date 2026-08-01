# LLMFoundry

The AI engineering kit for DeepSeek. Skills, standards, and quality gates for building
LLM systems — agents, RAG, evals, MCP — with production discipline: SPEC → TDD → worktree → atomic commit.

## Principles

1. **English** — everything in English.
2. **DeepSeek-optimized** — imperative tone, minimal guardrails, no hedging. Explicit
   structures compensate for the model's lower guardrails.
3. **Engineering standards** — verifiable output (`file:line`, command+output, validated schema).
4. **Mandatory dev pattern** — SPEC → TDD → git worktree → atomic commit.

## Model policy

| Role | Model | Requests/mo | Cost/MTok out |
|------|-------|-------------|----------------|
| Default | `opencode-go/deepseek-v4-pro` | 17,150 | $0.87 |
| small_model | `opencode-go/deepseek-v4-flash` | 158,150 | $0.28 |

Cost decision: DeepSeek family over kimi-k3 (53x cheaper, 35-322x more requests).

## Structure

```
skills/       # 17 skills (dev-process / ai-core / ai-advanced)
agents/       # deep-researcher, ai-architect, ai-evals-runner, llm-security-reviewer
commands/     # ai-spec, ai-build, ai-evals, ai-review, ai-research
references/   # shared checklists
evals/        # golden-sets + routing eval
plugins/      # gates (review-gate, egress-guard, test-gate, eval-gate)
scripts/      # install.sh (symlink into ~/.config/opencode)
```

## Install

```bash
./scripts/install.sh
```

Symlinks skills/, agents/, commands/ into `~/.config/opencode/`. Edit here, reflects live.

## License

MIT.
