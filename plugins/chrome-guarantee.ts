import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry chrome-guarantee: makes sure the chrome-devtools MCP always
 * connects to YOUR Chrome (with logins), never a separate clean one.
 *
 * Problem: --autoConnect only works when the Chrome DevToolsActivePort file
 * exists. If Chrome is not running with remote debugging, the MCP falls back
 * to launching a clean Chrome (no logins).
 *
 * Guarantee: before any browser tool is used, check that the debug endpoint
 * is alive. If not, restart YOUR Chrome (chrome-debug-profile, with logins)
 * with the debug port, then the MCP connects to it.
 *
 * Profile: ~/chrome-debug-profile, your personal profile with logins.
 */

import { execSync } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

const PROFILE = path.join(os.homedir(), "chrome-debug-profile");
const PORT = 9222;
const DEBUG_PORT_FILE = path.join(PROFILE, "DevToolsActivePort");

function isDebugAlive(): boolean {
  // The DevToolsActivePort file must exist AND the port must respond.
  if (!fs.existsSync(DEBUG_PORT_FILE)) return false;
  try {
    const port = Number(fs.readFileSync(DEBUG_PORT_FILE, "utf8").split("\n")[0]);
    execSync(`curl -s --max-time 2 http://127.0.0.1:${port}/json/version`, { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

function ensureChromeDebug(): void {
  if (isDebugAlive()) return;
  try {
    // Chrome already running without debug? We cannot restart it from here
    // without losing the user's windows, so log clearly instead.
    execSync("pgrep -x 'Google Chrome'", { stdio: "ignore" });
    console.error(
      "[chrome-guarantee] Chrome is running but WITHOUT the debug port. " +
        "Quit Chrome once, then the plugin will start it with the debug port " +
        "on the next launch. Until then the MCP may open a clean Chrome.",
    );
    return;
  } catch {
    // No Chrome running. Start YOUR Chrome (with logins) + debug port.
    try {
      execSync(
        `"${process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}" ` +
          `--remote-debugging-port=${PORT} --user-data-dir="${PROFILE}" --restore-last-session ` +
          // Stop the on-device AI model (OptGuideOnDeviceModel, ~4GB/profile) from being
          // re-downloaded every time. It powers local AI extras we do not use.
          `--disable-features=OptimizationGuideModelDownloading >/dev/null 2>&1 &`,
        { shell: "/bin/bash" },
      );
      console.error(`[chrome-guarantee] Started your Chrome with debug port ${PORT} (logins).`);
    } catch (e) {
      console.error("[chrome-guarantee] Failed to start Chrome:", String(e));
    }
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
