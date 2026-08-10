import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry delegation-guard — validates subagent spawns before they leave
 * the orchestrator.
 *
 * The 4 mandatory parts (Objective, Context, Output contract, Boundaries)
 * are HARD-BLOCKED when missing — this catches genuine delegation mistakes.
 * A well-formed prompt with the 4 parts is trusted: suspected misrouting by
 * keyword is surfaced as a WARNING to the session, never thrown, so legitimate
 * work cannot enter an infinite rewrite-retry loop.
 *
 * CIRCUIT BREAKER: additionally guards against a delegation that keeps
 * retrying the same target a its continues to fail. If N spawns hit the same
 * (session, subagent_type) within a short window, the guard trips and blocks
 * further spawns to that target for a cooldown (dead-letter) instead of
 * letting the orchestrator loop. This is the safety net for "guard fails ->
 * agent retries forever"; it breaks the loop at the source.
 */

// Circuit-breaker tuning. Per (session, target): allow up to MAX_SPAWNS spawns
// within TRIP_WINDOW_MS; if exceeded, trip and reject further spawns for
// COOLDOWN_MS. Detective: a transient failure must reset after the window.
const TRIP_WINDOW_MS = 60_000;
const MAX_SPAWNS = 3;
const COOLDOWN_MS = 120_000;

// key: `${sessionID}:${targetAgent}` -> { attempts: number[], trippedUntil: number }
const breakerState = new Map<
  string,
  { attempts: number[]; trippedUntil: number }
>();

function tripBreaker(sessionID: string, target: string): boolean {
  const now = Date.now();
  const key = `${sessionID}:${target}`;
  let st = breakerState.get(key);
  if (!st) {
    st = { attempts: [], trippedUntil: 0 };
    breakerState.set(key, st);
  }

  // If currently tripped, reject until cooldown expires.
  if (now < st.trippedUntil) return true;

  // Prune attempts older than the window, then count live ones.
  const cutoff = now - TRIP_WINDOW_MS;
  st.attempts = st.attempts.filter((t) => t >= cutoff);
  st.attempts.push(now);

  if (st.attempts.length > MAX_SPAWNS) {
    // Trip: reject for the cooldown, reset the counter so a later legit
    // spawn (after cooldown) starts fresh instead of tripping forever.
    st.trippedUntil = now + COOLDOWN_MS;
    st.attempts = [];
    return true;
  }
  return false;
}

const MANDATORY_PARTS: [string, RegExp][] = [
  ["Objective", /##\s*Objective/i],
  ["Context", /##\s*Context/i],
  ["Output contract", /##\s*Output contract/i],
  ["Boundaries", /##\s*Boundaries/i],
];

// Suspected misroutes. WARNING-ONLY now: these never throw.
// Rules require MULTIPLE strong signals to fire, to cut false positives on
// ordinary topic words that legitimately appear in a well-formed prompt.
// Every term is wrapped in \b...\b (word boundaries) so Portuguese verbs like
// "reconhecer" do not falsely match "recon".
const MISROUTE_RULES: [RegExp, string[]][] = [
  // market/competitive research only fires when TWO+ market terms appear together.
  [
    /\b(?:market|competitor|industry|pricing|adoption)\b.*\b(?:market|competitor|industry|pricing|adoption)\b/i,
    ["ai-architect", "ai-evals-runner", "llm-security-reviewer", "reverse-engineer"],
  ],
  [
    // a DESIGN/BUILD task (verb) never goes to evals or RE. High specificity.
    /\b(?:design|build|implement|system\s+design)\b.*\b(?:deploy|ship|write\s+code|implement)\b/i,
    ["ai-evals-runner", "reverse-engineer"],
  ],
  [
    // eval-related work only flags on the combination eval term + measurement term:
    // a lone "evals" topic (e.g. "estudo de avaliação de um documento") must NOT
    // fire; "eval task" + "assertion/score" is what actually means eval-routing.
    /\b(?:evaluation|evals?|eval\s+run|golden\s+set)\b.*\b(?:assertion|benchmark|metric|pass\s+rate|score)\b/i,
    ["deep-researcher", "ai-architect", "llm-security-reviewer", "reverse-engineer"],
  ],
  [
    // LLM security review is a high-confidence route only on precise phrase match.
    /\b(?:prompt\s+injection|OWASP|LLM\s+(?:app|security)\s+top\s+10)\b/i,
    ["deep-researcher", "ai-evals-runner", "reverse-engineer"],
  ],
  [
    // reverse-engineering requires the conjunction of a RE tool/domain term AND a
    // RE object, so "the installed binary" alone no longer fires.
    /\b(?:malware|firmware|ghidra|radare|decompil\w*|disassembl\w*|ida\s+pro)\b.*\b(?:malware|firmware|ghidra|radare|decompil\w*|disassembl\w*)\b/i,
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
): { status: "block" | "warn" | "pass"; message?: string } {
  // Gate 1: mandatory parts — the real protection. Missing parts HARD-BLOCK.
  const missing: string[] = [];
  for (const [name, re] of MANDATORY_PARTS) {
    if (!re.test(prompt)) missing.push(name);
  }
  if (missing.length > 0) {
    return {
      status: "block",
      message: `missing mandatory part${missing.length > 1 ? "s" : ""}: ${missing.join(", ")}. Rewrite with: ## Objective, ## Context, ## Output contract, ## Boundaries.`,
    };
  }

  // Gate 2: transversal consultation. When the orchestrator names 2+ distinct
  // agents in one prompt it is gathering multiple views on the same topic, not
  // misrouting a single task. Trust the explicit mention.
  if (distinctAgents(prompt) >= 2) {
    return { status: "pass" };
  }

  // Gate 3: research-first priority. A task that asks for research and is
  // routed to the researcher is correct, whatever its topic mentions.
  if (RESEARCH_SIGNALS.test(prompt) && targetAgent === "deep-researcher") {
    return { status: "pass" };
  }

  // Gate 4: suspected misroute — WARNING ONLY, never throws. The orchestrator's
  // explicit routing decision (in a prompt that already satisfies Gate 1) is
  // trusted over keyword heuristics that have produced false positives.
  for (const [re, blocked] of MISROUTE_RULES) {
    if (re.test(prompt) && blocked.includes(targetAgent)) {
      return {
        status: "warn",
        message:
          `Suspected misroute to ${targetAgent}: prompt contains "${re.source.replace(/\\[.+?]/g, "(...)" ).replace(/[()]/g, " ").slice(0, 60)}...". ` +
          `Confirm this is the intended target. This spawn will proceed.`,
      };
    }
  }

  return { status: "pass" };
}

export async function server(_input: PluginInput): Promise<Hooks> {
  return {
    "tool.execute.before": async ({ tool, sessionID, callID }, output) => {
      if (tool !== "task") return;
      const args = output.args ?? {};
      const prompt = (args.prompt ?? args.content ?? "") as string;
      const target = (args.subagent_type ?? "") as string;

      if (!prompt || !target) return;

      // Circuit breaker: if the orchestrator keeps spawning the same target in
      // a short window, it is retrying a failing delegation. Trip -> hard
      // dead-letter so the loop cannot continue. This runs BEFORE validation
      // because a loop is the more severe failure.
      if (tripBreaker(sessionID, target)) {
        throw new Error(
          `[delegation-guard] circuit breaker TRIPPED for ${target} (session ${sessionID}): ` +
            `>${MAX_SPAWNS} spawns in ${TRIP_WINDOW_MS / 1000}s. This looks like a ` +
            `repeated failing delegation, not independent work. Paused for ` +
            `${COOLDOWN_MS / 1000}s. Change approach (different agent, smaller slice, ` +
            `or escalate to the Owner) instead of retrying the same target.`,
        );
      }

      const result = validateDelegation(prompt, target);
      if (result.status === "block") {
        // Only genuine mistakes (missing mandatory parts) hard-block.
        throw new Error(`[delegation-guard] ${result.message}`);
      }
      if (result.status === "warn") {
        // Suspected misroute: surface the warning to the session WITHOUT
        // aborting the spawn, so legitimate work cannot enter a retry loop.
        try {
          const warnMsg = `[delegation-guard] ${result.message}`;
          console.error(warnMsg);
          await _input.client.session.prompt({
            path: { id: sessionID },
            body: {
              parts: [
                {
                  type: "text",
                  text: `Advisory (plugin note for context, not a directive): ${warnMsg}. Your spawn will proceed as routed.`,
                } as { type: "text"; text: string },
              ],
            },
          });
        } catch {
          // surfacing the advisory must never break the spawn
          console.error(`[delegation-guard] advisory (could not surface): ${result.message}`);
        }
      }
    },
  };
}

export default {
  id: "llmfoundry-delegation-guard",
  server,
};
