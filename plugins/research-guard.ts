import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry research-guard — enforces the research delegation policy.
 *
 * The orchestrator must delegate internet research to the deep-researcher
 * subagent. Direct webfetch/websearch calls from the orchestrator bypass
 * source triangulation, confidence scoring, and correlation — the entire
 * research quality stack.
 *
 * This guard fires a recoverable warning on every direct webfetch/websearch
 * call. The orchestrator sees it and delegates. The deep-researcher sees it
 * and continues (it's doing legitimate research). Context7 documentation
 * lookups pass through silently.
 *
 * If LF_RESEARCH_STRICT=1 is set, the guard BLOCKS (throws) instead of
 * warning — useful in CI or when you want hard enforcement.
 */

const STRICT = process.env.LF_RESEARCH_STRICT === "1";

const RESEARCH_KEYWORDS = /\b(?:research|compare|competitor|market|landscape|OSINT|recon)\b/i;

function isDocLookup(args: Record<string, unknown>): boolean {
  const url = (args.url ?? "") as string;
  // Context7 documentation lookups are not research
  if (url.includes("context7")) return true;
  // Specific documentation URLs are not research
  if (/\/docs?\/|\/api\/|readme|\.md$/i.test(url)) return true;
  return false;
}

function looksLikeResearch(args: Record<string, unknown>): boolean {
  const url = (args.url ?? "") as string;
  const query = (args.query ?? args.q ?? "") as string;
  const payload = JSON.stringify({ url, query });
  return RESEARCH_KEYWORDS.test(payload);
}

export async function server(_input: PluginInput): Promise<Hooks> {
  return {
    "tool.execute.before": async ({ tool, sessionID, callID }, output) => {
      if (tool !== "webfetch" && tool !== "websearch") return;
      const args = (output.args ?? {}) as Record<string, unknown>;

      // Documentation lookups are fine — only flag general research
      if (isDocLookup(args)) return;
      if (!looksLikeResearch(args)) return;

      const msg =
        `[research-guard] Direct ${tool} detected. Per research policy, ` +
        `internet research must go through the deep-researcher subagent ` +
        `(source triangulation + confidence scoring). Delegate this task.`;

      if (STRICT) {
        throw new Error(msg);
      }
      console.error(msg);
    },
  };
}

export default {
  id: "llmfoundry-research-guard",
  server,
};
