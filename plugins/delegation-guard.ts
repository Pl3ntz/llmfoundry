import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry delegation-guard — validates subagent spawns before they leave
 * the orchestrator.
 *
 * Catches the two most common delegation failures:
 * 1. Spawning without the 4 mandatory parts (Objective, Context, Output
 *    contract, Boundaries) — the subagent guesses and wastes tokens.
 * 2. Clear misrouting — e.g., a research task going to ai-architect, or
 *    an eval task going to deep-researcher.
 *
 * Blocks are recoverable: the spawn is rejected with an error message that
 * tells the orchestrator what to fix. The orchestrator rewrites and retries.
 *
 * Does NOT attempt to validate every possible route — routing decisions that
 * depend on task semantics (vs clear keyword mismatch) remain the model's
 * responsibility.
 */

const MANDATORY_PARTS: [string, RegExp][] = [
  ["Objective", /##\s*Objective/i],
  ["Context", /##\s*Context/i],
  ["Output contract", /##\s*Output contract/i],
  ["Boundaries", /##\s*Boundaries/i],
];

// Clear misroutes: if prompt matches these patterns, it must NOT go to the listed agents.
// Design principle: keywords are TOPICS (what the task is about), verbs are TASKS
// (what to do). Only verbs should misroute. "agents", "MCP", "RAG" are topics that
// legitimately appear in research prompts ("research AI agent frameworks"),
// so they must never block a deep-researcher spawn.
//
// Every alternative here is wrapped in \b...\b (word boundaries). Without them,
// a Portuguese verb like "reconhecer" contains "recon" and falsely triggers the
// market-research rule, blocking legit design/security/evals spawns.
const MISROUTE_RULES: [RegExp, string[]][] = [
  [
    // market/competitive/landscape research does not go to architects, evals, security, RE
    /\b(?:market|competitor|landscape|industry|pricing|adoption|OSINT|recon)\b/i,
    ["ai-architect", "ai-evals-runner", "llm-security-reviewer", "reverse-engineer"],
  ],
  [
    // a DESIGN/BUILD task (verb) does not go to evals or RE
    // deep-researcher is NOT blocked here: a prompt may contain "architecture" or
    // "design" as a topic while still being a research task.
    /\b(?:design|architect(?:ure|ing|s)?|build|implement|system\s+design|spec\s+for)\b/i,
    ["ai-evals-runner", "reverse-engineer"],
  ],
  [
    // eval/evals/evaluation. \bevals?\b keeps "ai-evals-runner" (mentioned as a
    // topic in a multi-agent prompt) from matching — handled by the debate gate.
    /\b(?:eval(?:s|uation)?|golden\s+set|regression|baseline|assertion|prompt.*(?:change|update))\b/i,
    ["deep-researcher", "ai-architect", "llm-security-reviewer", "reverse-engineer"],
  ],
  [
    /\b(?:security\s+review|prompt\s+injection|OWASP|LLM\s+(?:app\s+)?security)\b/i,
    ["deep-researcher", "ai-evals-runner", "reverse-engineer"],
  ],
  [
    /\b(?:binary|firmware|malware|decompil\w*|disassembl\w*|ghidra|radare)\b/i,
    ["deep-researcher", "ai-architect", "ai-evals-runner", "llm-security-reviewer"],
  ],
];

// Strong research signals: when present, deep-researcher is a VALID route no
// matter which topic words appear in the prompt ("research MCP servers").
// "pesquis\w*" matches Portuguese "pesquisa/pesquisar/pesquisador".
const RESEARCH_SIGNALS = /\b(?:research|compare|landscape|market|competitor|industry|OSINT|recon|pesquis\w*)\b/i;

// Known subagents. When 2+ distinct agents are named in a single prompt, the
// orchestrator is deliberately running a transversal consultation (a debate
// over the same topic), not misrouting a single task. Agent names there are
// TOPICS, not the task target, so misroute rules must not fire.
const AGENT_NAMES = [
  "deep-researcher", "ai-architect", "ai-evals-runner", "llm-security-reviewer",
  "reverse-engineer", "platform-engineer", "backend-architect", "api-contract-engineer",
  "database-engineer", "data-model-engineer", "red-team-agent", "security-defensive",
  "bug-bounty-hunter", "recon-agent", "report-agent", "triage-agent", "general", "explore",
];
const AGENT_MENTION = new RegExp(`\\b(?:${AGENT_NAMES.join("|")})\\b`, "gi");

function distinctAgents(prompt: string): number {
  return new Set(prompt.match(AGENT_MENTION) ?? []).size;
}

function validateDelegation(
  prompt: string,
  targetAgent: string,
): string | null {
  // Gate 1: mandatory parts
  const missing: string[] = [];
  for (const [name, re] of MANDATORY_PARTS) {
    if (!re.test(prompt)) missing.push(name);
  }
  if (missing.length > 0) {
    return `Delegation blocked: missing mandatory part${missing.length > 1 ? "s" : ""}: ${missing.join(", ")}. Rewrite with: ## Objective, ## Context, ## Output contract, ## Boundaries.`;
  }

  // Gate 2: transversal consultation. When the orchestrator names 2+ distinct
  // agents in one prompt it is gathering multiple views on the same topic, not
  // misrouting a single task. Trust the explicit mention.
  if (distinctAgents(prompt) >= 2) {
    return null;
  }

  // Gate 3: research-first priority. A task that asks for research and is
  // routed to the researcher is correct, whatever its topic mentions.
  if (RESEARCH_SIGNALS.test(prompt) && targetAgent === "deep-researcher") {
    return null;
  }

  // Gate 4: clear misroutes
  for (const [re, blocked] of MISROUTE_RULES) {
    if (re.test(prompt) && blocked.includes(targetAgent)) {
      return `Delegation blocked: prompt appears to be about "${re.source.replace(/[()]/g, "").replace(/\|\?/g, "").slice(0, 60)}..." but was routed to ${targetAgent}. This is likely a misroute. Check the routing table.`;
    }
  }

  return null; // pass
}

export async function server(_input: PluginInput): Promise<Hooks> {
  return {
    "tool.execute.before": async ({ tool, sessionID, callID }, output) => {
      if (tool !== "task") return;
      const args = output.args ?? {};
      const prompt = (args.prompt ?? args.content ?? "") as string;
      const target = (args.subagent_type ?? "") as string;

      if (!prompt || !target) return;

      const reason = validateDelegation(prompt, target);
      if (reason) {
        throw new Error(`[delegation-guard] ${reason}`);
      }
    },
  };
}

export default {
  id: "llmfoundry-delegation-guard",
  server,
};
