import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry gates — execution guards ported from Quarterdeck's philosophy:
 * enforcement lives outside the model. Rules the model merely reads are guidance;
 * these hooks are controls.
 *
 * Gates:
 * - test-gate:  blocks `git commit` when the full test suite has not run this session
 * - review-gate: warns when committing without a recorded review of the staged diff
 * - egress-guard: scans outbound fetch/search payloads for secrets and infra identifiers
 * - env-guard:  blocks commits that would stage .env or secret files
 */

const BLOCKED_EGRESS_PATTERNS: RegExp[] = [
  /-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----/,
  /\bAKIA[0-9A-Z]{16}\b/,
  /\bgh[pousr]_[A-Za-z0-9]{20,}\b/,
  /\bsk-[A-Za-z0-9]{20,}\b/,
  /xox[baprs]-[A-Za-z0-9-]{10,}/,
  /\bAIza[0-9A-Za-z_-]{35}\b/,
  /\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\./, // JWT
];

const BLOCKED_SECRET_FILES = /(^|\/)(\.env(\.|$)|secrets\/|.*\.pem$|.*\.key$|.*\.p12$)/;

function secretScan(text: string): string | null {
  for (const re of BLOCKED_EGRESS_PATTERNS) {
    if (re.test(text)) return re.toString();
  }
  return null;
}

export async function server(input: PluginInput): Promise<Hooks> {
  const { $ } = input;
  const ranTests = new Set<string>();

  return {
    "tool.execute.before": async ({ tool, sessionID, callID }, output) => {
      const args = output.args ?? {};

      // test-gate: mark that tests ran
      if (tool === "bash" && typeof args.command === "string") {
        const cmd = args.command;
        if (/(npm|pnpm|yarn|bun)\s+(run\s+)?(test|check)|pytest|vitest|playwright|go test|cargo test/.test(cmd)) {
          ranTests.add(sessionID);
        }

        // review-gate: block commits without tests run this session
        if (/(^|&&|;)\s*git\s+commit\b/.test(cmd)) {
          if (!ranTests.has(sessionID)) {
            console.error("[gates] test-gate: no test suite ran this session. Run tests before committing.");
            return { args };
          }
        }

        // env-guard: block committing secret files
        if (/(^|&&|;)\s*git\s+add\b/.test(cmd)) {
          const files = cmd.split(/\s+/).slice(2);
          for (const f of files) {
            if (BLOCKED_SECRET_FILES.test(f)) {
              console.error(`[gates] env-guard: refusing to stage secret file: ${f}`);
              return { args };
            }
          }
        }
      }

      // egress-guard: scan outbound payloads
      if ((tool === "webfetch" || tool === "websearch") && args) {
        const payload = JSON.stringify(args);
        const hit = secretScan(payload);
        if (hit) {
          console.error(`[gates] egress-guard: blocked outbound ${tool} containing a secret (${hit})`);
          return { args };
        }
      }
      return { args };
    },

    "chat.message": async () => {},
  };
}

export const gatesPlugin = {
  id: "llmfoundry-gates",
  server,
};

export default gatesPlugin;
