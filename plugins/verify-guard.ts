import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry verify-guard — flags output that asserts facts without evidence
 * (delirium). Enforcement lives outside the model.
 *
 * Scans tool OUTPUT for:
 * - conjecture-as-grounding: "probably", "should be", "likely", "seems",
 *   "i assume", "i believe", "as far as i know", "must be"
 * - unverified facts in prose (no confidence marker, no proof citation)
 *
 * Blocks are recoverable: the agent sees what was flagged and rewrites with
 * evidence or an honest [UNVERIFIED] marker (see skill anti-delirium).
 */

const HEDGE_AS_GROUNDING: RegExp[] = [
  /\bprobably\b/i,
  /\bshould be\b/i,
  /\blikely\b/i,
  /\bseems?\s+(to\s+be\s+)?(that\s+|like\s+)/i,
  /\bappears?\s+to\s+be\b/i,
  /\bi assume\b/i,
  /\bi believe\b/i,
  /\b(i\s+)?think\s+it(\s+is)?\b/i,
  /\bas far as i know\b/i,
  /\bmust be\b/i,
  /\bprobably\b/i,
  /\broughly\b(?=\s+[a-z])/i,
];

function hedgeHits(text: string): string[] {
  const found: string[] = [];
  for (const re of HEDGE_AS_GROUNDING) {
    if (re.test(text)) found.push(re.source.replace(/\\b|\/\w+/gi, "").replace(/[()]/g, ""));
  }
  return found;
}

export async function server(input: PluginInput): Promise<Hooks> {
  return {
    "tool.execute.after": async ({ tool, callID, args }, output) => {
      if (tool === "write" || tool === "edit") {
        const filePath = (args?.filePath ?? args?.path ?? "") as string;
        // Only prose/documentation files — code files legitimately have different grammar
        if (!/\.(md|txt|mdx)$/.test(filePath)) return;
        const content = (output.output || "") as string;
        // Skip structured findings blocks (they carry explicit severity + evidence)
        if (content.includes("### FINDINGS")) return;
        const hits = hedgeHits(content);
        if (hits.length > 0) {
          console.error(
            `[verify-guard] WARNING: ${filePath} contains conjecture as grounding (${hits.slice(0, 4).join(", ")}). ` +
              `Per anti-delirium: verify the claim or mark it [UNVERIFIED]. Review before shipping.`,
          );
        }
      }
    },
  };
}

export default {
  id: "llmfoundry-verify-guard",
  server,
};
