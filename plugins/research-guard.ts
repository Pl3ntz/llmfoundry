import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry research-guard — enforces the research delegation policy.
 *
 * The orchestrator must delegate internet research to the deep-researcher-v2
 * subagent. Direct webfetch/websearch calls from the ORCHESTRATOR bypass
 * source triangulation, confidence scoring, and correlation — the entire
 * research quality stack.
 *
 * This guard fires a recoverable warning ONLY when the research-looking call
 * comes from a root session (the orchestrator). Subagents run in child
 * sessions (Session.parentID set), so the deep-researcher-v2 does legitimate
 * research without ever being nagged. Context7 and doc lookups pass silently.
 *
 * If LF_RESEARCH_STRICT=1 is set, the guard BLOCKS (throws) instead of
 * warning — useful in CI or when you want hard enforcement.
 */

const STRICT = process.env.LF_RESEARCH_STRICT === "1";

// Strong signals of market/competitive/OSINT research. "research" and "compare"
// alone are too ambiguous (a query like "compare bun vs node" is a doc lookup),
// so they are not in this list.
const RESEARCH_KEYWORDS =
  /\b(?:market|competitor|landscape|industry|pricing|adoption|OSINT|recon|vs\.?\.?\s+alternatives?)\b/i;

// Doc/technical lookup terms. A websearch has no URL, so the guard must read the
// query too: "fastapi vs flask docs", "install bun", "setup MCP server" are NOT
// market research.
const DOC_TERMS =
  /\b(?:docs?|documentation|api|guide|tutorial|reference|getting\s+started|setup|install|config|example|how\s+to|library|framework|sdk|syntax|error|changelog|release|npm|pypi|crates)\b/i;

function isDocLookup(args: Record<string, unknown>): boolean {
  const url = (args.url ?? "") as string;
  const query = (args.query ?? args.q ?? "") as string;
  // Context7 documentation lookups are not research
  if (url.includes("context7")) return true;
  // Specific documentation URLs are not research
  if (/\/docs?\/|\/api\/|readme|\.md$/i.test(url)) return true;
  // Query-only lookups (websearch): technical/doc intent is not research
  if (query && DOC_TERMS.test(query)) return true;
  return false;
}

function looksLikeResearch(args: Record<string, unknown>): boolean {
  const url = (args.url ?? "") as string;
  const query = (args.query ?? args.q ?? "") as string;
  const payload = JSON.stringify({ url, query });
  return RESEARCH_KEYWORDS.test(payload);
}

export async function server(input: PluginInput): Promise<Hooks> {
  const { client } = input;
  return {
    "tool.execute.before": async ({ tool, sessionID, callID }, output) => {
      if (tool !== "webfetch" && tool !== "websearch") return;
      const args = (output.args ?? {}) as Record<string, unknown>;

      // Documentation lookups are fine — only flag general research
      if (isDocLookup(args)) return;
      if (!looksLikeResearch(args)) return;

      // Subagents (deep-researcher-v2) run in child sessions (parentID set).
      // Their research is the whole point of the policy — never nag them.
      // Only a root session (the orchestrator fetching directly) is warned.
      let isChildSession = false;
      try {
        const session = await client.session.get({ path: { id: sessionID } });
        const data = session as {
          data?: { parentID?: string | null };
          parentID?: string | null;
        };
        isChildSession = Boolean(data?.data?.parentID ?? data?.parentID);
      } catch {
        // a lookup failure must never break the tool call
      }
      if (isChildSession) return;

      const msg =
        `[research-guard] Direct ${tool} detected in the root session. Per ` +
        `research policy, internet research must go through the ` +
        `deep-researcher-v2 subagent (source triangulation + confidence ` +
        `scoring). Delegate this task.`;

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
