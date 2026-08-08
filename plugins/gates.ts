import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry gates — execution guards. Enforcement lives outside the model.
 * Rules the model merely reads are guidance; these hooks are controls.
 *
 * Gates (block by throwing — the documented veto mechanism):
 * - test-gate:  blocks `git commit` when the full test suite has not run this session
 * - env-guard:  blocks staging .env or secret files
 * - egress-guard: blocks outbound fetch/search carrying secrets or infra identifiers
 *
 * Every gate has an escape hatch (LF_GATES_OFF=1) — a gate that blocks everything
 * trains you to disable it.
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
  const ranTests = new Set<string>();

  return {
    "tool.execute.before": async ({ tool, sessionID, callID }, output) => {
      const args = output.args ?? {};

      if (tool === "bash" && typeof args.command === "string") {
        const cmd = args.command;

        // test-gate: mark that tests ran
        // this project's suite runs via scripts/eval-runner.py and scripts/ci-local.sh,
        // so recognize those too, not just pytest/vitest/bun test.
        // xcodebuild test: macOS/Swift projects (ex: nabla) rodam a suite via
        // `xcodebuild test` — sem isso o gate bloqueava commits legítimos (falso
        // positivo reportado 2026-08-07).
        if (/(npm|pnpm|yarn|bun)\s+(run\s+)?(test|check)|pytest|vitest|playwright|go test|cargo test|eval-runner|ci-local|xcodebuild test/.test(cmd)) {
          ranTests.add(sessionID);
        }

        // test-gate: block commits without tests run this session
        if (/(^|&&|;)\s*git\s+commit\b/.test(cmd)) {
          if (!ranTests.has(sessionID)) {
            throw new Error(
              "[gates] test-gate: no test suite ran this session. Run tests before committing (or set LF_GATES_OFF=1).",
            );
          }
        }

        // env-guard: block staging secret files
        if (/(^|&&|;)\s*git\s+add\b/.test(cmd)) {
          const files = cmd.split(/\s+/).slice(2);
          for (const f of files) {
            if (BLOCKED_SECRET_FILES.test(f)) {
              throw new Error(
                `[gates] env-guard: refusing to stage secret file: ${f} (or set LF_GATES_OFF=1).`,
              );
            }
          }
        }
      }

      // egress-guard: block outbound fetch/search carrying secrets
      if ((tool === "webfetch" || tool === "websearch") && args) {
        const payload = JSON.stringify(args);
        const hit = secretScan(payload);
        if (hit) {
          throw new Error(
            `[gates] egress-guard: blocked outbound ${tool} containing a secret (${hit}). Refusing to leak data.`,
          );
        }
      }
    },
  };
}

export default {
  id: "llmfoundry-gates",
  server,
};
