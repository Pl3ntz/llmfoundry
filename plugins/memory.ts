import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry memory plugin — the runtime of the living feedback loop.
 *
 * FEED (encode): observes tool executions and captures structured signals:
 *   - bash failure output → gotcha
 *   - git commit → memory event
 *
 * CONSUME (retrieve): injects the recall preamble into the system prompt via
 *   experimental.chat.system.transform, so the model sees relevant open
 *   findings + recurring gotchas before acting — like human recall.
 *
 * Local-only. Data lives in ~/.local/share/llmfoundry/memory/ — never versioned.
 */

const MEMORY_BIN =
  (process.env.HOME || "") + "/dev/llmfoundry/scripts/memory/foundry_memory.py";
const PY = "python3";

async function run(args: string[]): Promise<string> {
  try {
    const p = Bun.spawnSync([PY, MEMORY_BIN, ...args], {
      stdout: "pipe",
      stderr: "pipe",
      cwd: process.env.HOME || "/",
    });
    return (p.stdout?.toString() || "").trim();
  } catch {
    return "";
  }
}

function looksLikeError(output: string): boolean {
  return (
    /failed|error|exception|traceback|not found|exit code|timed out/i.test(output) &&
    !/^0$/.test(output.trim())
  );
}

export async function server(input: PluginInput): Promise<Hooks> {
  return {
    // ---- ENCODE: capture signals from tool execution ----
    "tool.execute.after": async ({ tool, sessionID, callID, args }, output) => {
      if (tool !== "bash" || typeof args.command !== "string") return;
      const cmd = args.command;
      const out = output.output || "";

      // Capture bash failures as gotchas
      if (looksLikeError(out) && cmd.length < 300) {
        const pattern = cmd.split(/\s+/).slice(0, 4).join(" ");
        await run([
          "gotcha", "default", pattern,
          "--category", "bash-error",
          "--sample", out.slice(0, 200),
        ]);
      }

      // Capture commits as memory events
      if (/(^|&&|;)\s*git\s+commit\b/.test(cmd) && out) {
        const m = out.match(/(feat|fix|refactor|docs|test|chore|perf|ci)[^:]*:\s*[^\n]*/);
        if (m) {
          await run(["remember", `commit: ${m[0]}`, "--container", "default", "--type", "commit"]);
        }
      }
    },

    // ---- RETRIEVE: inject recall preamble into the system prompt ----
    "experimental.chat.system.transform": async (_input, output) => {
      const recall = await run(["recall", "--top", "5"]);
      if (!recall.trim() || recall.includes("=== FINDINGS ===") === false) {
        return;
      }
      const preamble =
        "\n\n---foundry-memory---\n" +
        recall +
        "\n---end-foundry-memory---\n" +
        "Above is relevant past memory (open findings and recurring gotchas). " +
        "Use it as context; do not restate it. If an open finding is relevant, act on it.";
      output.system.push(preamble);
    },
  };
}

export default {
  id: "llmfoundry-memory",
  server,
};
