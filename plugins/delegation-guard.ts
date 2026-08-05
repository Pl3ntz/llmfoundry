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
const MISROUTE_RULES: [RegExp, string[]][] = [
  [
    // market/competitive/landscape research does not go to architects, evals, security, RE
    /(?:market|competitor|landscape|industry|pricing|adoption|OSINT|recon)/i,
    ["ai-architect", "ai-evals-runner", "llm-security-reviewer", "reverse-engineer"],
  ],
  [
    // a DESIGN/BUILD task (verb) does not go to evals or RE
    // deep-researcher is NOT blocked here: a prompt may contain "architecture" or
    // "design" as a topic while still being a research task.
    /(?:design|architect(?:ure|ing)?|build|implement|system\s+design|spec\s+for)/i,
    ["ai-evals-runner", "reverse-engineer"],
  ],
  [
    /(?:eval|golden.set|regression|baseline|assertion|prompt.*(?:change|update))/i,
    ["deep-researcher", "ai-architect", "llm-security-reviewer", "reverse-engineer"],
  ],
  [
    /(?:security\s+review|prompt\s+injection|OWASP|LLM\s+(?:app\s+)?security)/i,
    ["deep-researcher", "ai-evals-runner", "reverse-engineer"],
  ],
  [
    /(?:binary|firmware|malware|decompil|disassembl|ghidra|radare)/i,
    ["deep-researcher", "ai-architect", "ai-evals-runner", "llm-security-reviewer"],
  ],
];

// Strong research signals: when present, deep-researcher is a VALID route no
// matter which topic words appear in the prompt ("research MCP servers").
const RESEARCH_SIGNALS = /(?:research|compare|landscape|market|competitor|industry|OSINT|recon|pesquis)/i;

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

  // Gate 2: research-first priority. A task that asks for research and is
  // routed to the researcher is correct, whatever its topic mentions.
  if (RESEARCH_SIGNALS.test(prompt) && targetAgent === "deep-researcher") {
    return null;
  }

  // Gate 3: clear misroutes
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
