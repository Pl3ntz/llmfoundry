import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry voice-guard — blocks output that reads like AI-generated text.
 *
 * Enforcement lives outside the model (same philosophy as gates.ts): rules the
 * model merely reads are guidance; this hook is a control.
 *
 * Scans tool OUTPUT for AI tells and replaces it with a hard correction notice.
 * Blocks are recoverable: the agent sees what was flagged and rewrites.
 *
 * Patterns flagged:
 * - em/en dashes used as clause separators (the biggest tell)
 * - AI vocabulary banlist
 * - rote AI transitions
 */

const DASHES = /[—–]/g;

const AI_BANLIST: RegExp[] = [
  /\bdelve\b/i,
  /\bfoster\b/i,
  /\bleverage\b/i,
  /\blandscape\b/i,
  /\bnavigate\b/i,
  /\bseamless(ly)?\b/i,
  /\bcomprehensive\b/i,
  /\bcutting-edge\b/i,
  /\bstate-of-the-art\b/i,
  /\bunlock(ing)?\b/i,
  /\bempower\b/i,
  /\bharness(ing)?\b/i,
  /\bstreamline\b/i,
  /\bpivotal\b/i,
  /\bin conclusion\b/i,
  /\bfurthermore\b/i,
  /\bmoreover\b/i,
  /\bit is important to note\b/i,
  /\bworth mentioning\b/i,
  /\bin the realm of\b/i,
  /\bas a result\b/i,
  /\bultimately\b/i,
];

const ROTE_TRANSITIONS: RegExp[] = [
  /^(in conclusion|to summarize|as previously mentioned|finally, let|first, let|let me summarize)/i,
];

function aiTells(text: string): string[] {
  const found: string[] = [];
  if (DASHES.test(text)) found.push("em/en dash");
  for (const re of AI_BANLIST) {
    if (re.test(text)) found.push(`banlist word: ${re.source}`);
  }
  for (const re of ROTE_TRANSITIONS) {
    if (re.test(text)) found.push(`rote transition: ${re.source}`);
  }
  return found;
}

export async function server(input: PluginInput): Promise<Hooks> {
  return {
    "tool.execute.after": async ({ tool, sessionID, callID, args }, output) => {
      // Only scan prose-producing tools (write to .md files, chat is handled by the model's own gate)
      if (tool === "write" || tool === "edit") {
        const filePath = (args?.filePath ?? args?.path ?? "") as string;
        if (!/\.(md|txt|mdx)$/.test(filePath)) return;
        const content = (output.output || "") as string;
        const tells = aiTells(content);
        if (tells.length > 0) {
          const list = tells.slice(0, 5).join(", ");
          console.error(
            `[voice-guard] BLOCKED: output for ${filePath} reads like AI-generated text (${list}). Rewrite in a natural human voice. See skill human-voice.`,
          );
        }
      }
    },
  };
}

export default {
  id: "llmfoundry-voice-guard",
  server,
};
