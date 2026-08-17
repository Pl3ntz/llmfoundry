import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry chrome-guarantee: makes sure the chrome-devtools MCP always
 * connects to YOUR Chrome (with logins), never a separate clean one.
 *
 * Uses a DEDICATED debug profile (~/chrome-debug-profile) so it never
 * interferes with your normal Chrome / other opencode sessions.
 *
 * Robust fix for the "orphan DevToolsActivePort" bug: when the debug endpoint
 * file exists but the CDP server on that port is DEAD (a zombie process holds
 * the port but the JSON endpoint does not respond), the old code considered it
 * alive (because curl exits 0 even on an empty response). This made the MCP
 * connect to a dead browser and fail with "could not connect".
 *
 * The fix:
 *   1. isDebugAlive() actually checks that /json/version RETURNS content
 *      (not just that the process exits 0).
 *   2. If the endpoint is orphaned, we remove the DevToolsActivePort file
 *      (NOT the process) so the next autoConnect starts clean.
 *   3. We never kill your Chrome and never start a second one if one alive
 *      debug chrome already exists — this avoids breaking other sessions.
 */

import { execSync } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

const PROFILE = path.join(os.homedir(), "chrome-debug-profile");
// Porta 9223 (NAO 9222): o Chrome normal pode segurar o socket IPv4 da 9222
// como zombie (porta escuta mas CDP morto). Usar 9223 isola o debug-profile e
// evita conflito com o seu Chrome de operacoes.
const PORT = 9223;
const DEBUG_PORT_FILE = path.join(PROFILE, "DevToolsActivePort");

function debugPortFromFile(): number | null {
  if (!fs.existsSync(DEBUG_PORT_FILE)) return null;
  try {
    const first = fs.readFileSync(DEBUG_PORT_FILE, "utf8").split("\n")[0].trim();
    const port = Number(first);
    return Number.isInteger(port) && port > 0 && port <= 65535 ? port : null;
  } catch {
    return null;
  }
}

function cdpAlive(port: number): boolean {
  // CDP is alive only if the JSON endpoint ACTUALLY returns content.
  try {
    const out = execSync(
      `curl -s --max-time 2 http://127.0.0.1:${port}/json/version`,
      { encoding: "utf8" },
    ).trim();
    return out.length > 0 && out.includes("Browser");
  } catch {
    return false;
  }
}

function isDebugAlive(): boolean {
  // Checa o CDP NA PORTA FIXA (9223, a mesma que o MCP usa via browserUrl).
  // NAO depende do arquivo DevToolsActivePort: com --browserUrl o arquivo pode
  // nem existir, mas se o Chrome debug ja esta aberto e respondendo, devemos
  // REUTILIZAR (nao iniciar de novo). È exatamente o comportamento pedido:
  // primeiro ve se ja esta aberto, so abre novo se nao estiver.
  return cdpAlive(PORT);
}

function removeOrphanPortFile(): void {
  // A zombie process may hold the port, but the CDP endpoint is dead.
  // Remove the stale DevToolsActivePort so autoConnect starts clean next time.
  try {
    if (fs.existsSync(DEBUG_PORT_FILE)) {
      fs.unlinkSync(DEBUG_PORT_FILE);
      console.error("[chrome-guarantee] Removed orphan DevToolsActivePort (CDP dead).");
    }
  } catch (e) {
    console.error("[chrome-guarantee] Could not remove orphan port file:", String(e));
  }
}

function profileChromeRunning(): boolean {
  // Is a Chrome using our debug-profile already running? (distinguish from your
  // normal Chrome by the user-data-dir flag.)
  try {
    const out = execSync(
      "ps ax -o command=", { encoding: "utf8" },
    );
    return out.includes("--remote-debugging-port") && out.includes("chrome-debug-profile");
  } catch {
    return false;
  }
}

function ensureChromeDebug(): void {
  // 1. Already alive? nothing to do.
  if (isDebugAlive()) return;

  // 2. Port file exists but CDP dead -> orphan. Clean it so we don't fight it.
  if (debugPortFromFile() !== null) {
    removeOrphanPortFile();
  }

  // 3. Debug-profile Chrome running but WITHOUT a working debug port: it was
  //    started in some session without the flag (orphan). We cannot kill it
  //    (owner may be using it / house rule), and starting a second one would
  //    fight for the port. Clean the stale port file so nothing points to a
  //    dead endpoint, and surface a clear instruction to restart just the
  //    DEBUG profile (separate from the normal Chrome, so operations continue).
  try {
    const out = execSync("ps ax -o command=", { encoding: "utf8" });
    const debugChrome = out.includes("chrome-debug-profile");
    const alive = isDebugAlive();
    if (debugChrome && !alive) {
      removeOrphanPortFile();
      console.error(
        "[chrome-guarantee] Debug-profile Chrome is running but WITHOUT a live debug port. " +
          "Quit just that profile once (it is separate from your normal Chrome), " +
          "and this plugin will restart it with the debug port on the next browser tool. " +
          "Your normal Chrome is untouched.",
      );
      return; // don't start a duplicate while the debug-profile Chrome exists
    }
  } catch {
    /* ignore */
  }

  // 4. No debug-profile Chrome alive with CDP: start it clean.
  if (profileChromeRunning()) return; // another session already started it
  try {
    execSync(
      `"${process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}" ` +
        `--remote-debugging-port=${PORT} --user-data-dir="${PROFILE}" --restore-last-session ` +
        `--disable-features=OptimizationGuideModelDownloading >/dev/null 2>&1 &`,
      { shell: "/bin/bash" },
    );
    // Give it a moment to write DevToolsActivePort.
    try {
      execSync("sleep 3", { stdio: "ignore" });
    } catch {
      /* ignore */
    }
    // If after this it's still not alive, surface clearly.
    if (!isDebugAlive()) {
      console.error(
        `[chrome-guarantee] Started debug profile but CDP still not alive on ${PORT}. ` +
          "Check ~/chrome-debug-profile/DevToolsActivePort.",
      );
    } else {
      console.error(`[chrome-guarantee] Chrome debug profile active on port ${PORT} (logins).`);
    }
  } catch (e) {
    console.error("[chrome-guarantee] Failed to start Chrome:", String(e));
  }
}

export async function server(input: PluginInput): Promise<Hooks> {
  return {
    "tool.execute.before": async ({ tool }) => {
      if (tool === "chrome-devtools" || tool === "browser_navigate" || tool === "browser_*") {
        ensureChromeDebug();
      }
    },
  };
}

export default {
  id: "llmfoundry-chrome-guarantee",
  server,
};
