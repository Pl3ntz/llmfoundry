import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry chrome-guarantee: makes sure the chrome-devtools MCP connects to
 * YOUR Chrome (the one with your logins, tabs, extensions), opening a NEW TAB
 * inside your existing window — never a separate clean window/instance.
 *
 * Strategy (mirrors Claude Code): the MCP runs with `--autoConnect`, which
 * reads Chrome's `DevToolsActivePort` from the DEFAULT user data dir and
 * connects via WebSocket to the already-running Chrome. Chrome 144+ exposes
 * this endpoint when "Discover network targets" / remote debugging is enabled
 * via chrome://inspect/#remote-debugging — NO terminal flag needed.
 *
 * The plugin's job is ONLY to verify the endpoint is reachable before the
 * browser tool runs, and to surface a clear instruction if it is not. It
 * never kills Chrome and never starts a duplicate instance (owner opens
 * Chrome normally from the dock; asking for terminal flags is a non-goal).
 */

import { execSync } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

const PORT_FILE = path.join(
  os.homedir(),
  "Library/Application Support/Google/Chrome/DevToolsActivePort",
);

function debugPortFromFile(): number | null {
  if (!fs.existsSync(PORT_FILE)) return null;
  try {
    const first = fs.readFileSync(PORT_FILE, "utf8").split("\n")[0].trim();
    const port = Number(first);
    return Number.isInteger(port) && port > 0 && port <= 65535 ? port : null;
  } catch {
    return null;
  }
}

function debugPathFromFile(): string | null {
  if (!fs.existsSync(PORT_FILE)) return null;
  try {
    const lines = fs.readFileSync(PORT_FILE, "utf8").split("\n").map((l) => l.trim()).filter(Boolean);
    return lines.length >= 2 ? lines[1] : null;
  } catch {
    return null;
  }
}

async function cdpViaWsAliveAsync(port: number, wsPath: string): Promise<boolean> {
  return new Promise((resolve) => {
    const net = require("node:net");
    const crypto = require("node:crypto");
    const sock = net.connect(port, "127.0.0.1");
    const timer = setTimeout(() => { try { sock.destroy(); } catch {} resolve(false); }, 5000);
    sock.on("connect", () => {
      const key = crypto.randomBytes(16).toString("base64");
      sock.write(
        `GET ${wsPath} HTTP/1.1\r\nHost: 127.0.0.1:${port}\r\n` +
          "Upgrade: websocket\r\nConnection: Upgrade\r\n" +
          `Sec-WebSocket-Key: ${key}\r\nSec-WebSocket-Version: 13\r\n\r\n`,
      );
    });
    let data = "";
    sock.on("data", (c: Buffer) => {
      data += c.toString();
      if (data.includes("101")) {
        clearTimeout(timer);
        try { sock.destroy(); } catch {}
        resolve(true);
      }
    });
    sock.on("error", () => { clearTimeout(timer); resolve(false); });
    sock.on("timeout", () => { clearTimeout(timer); resolve(false); });
    sock.setTimeout(5000);
  });
}

async function isDebugAlive(): Promise<boolean> {
  const port = debugPortFromFile();
  const wsPath = debugPathFromFile();
  if (port === null || wsPath === null) return false;
  return cdpViaWsAliveAsync(port, wsPath);
}

async function ensureChromeDebug(): Promise<void> {
  // 1. Seu Chrome ja expoe o endpoint WebSocket (DevToolsActivePort)? Nada a
  //    fazer: o MCP (--autoConnect) conecta sozinho na sua janela.
  if (await isDebugAlive()) return;

  // 2. Endpoint indisponível: NUNCA matamos seu Chrome e NUNCA iniciamos uma
  //    instancia separada. O Chrome 144+ precisa apenas de remote debugging
  //    habilitado via chrome://inspect — instrucao clara, zero terminal.
  const hasPortFile = fs.existsSync(PORT_FILE);
  console.error(
    "[chrome-guarantee] Nao achei o WebSocket de debug do seu Chrome aberto. " +
      "Para eu trabalhar na MESMA janela (abas novas dentro dela), " +
      "abra a pagina chrome://inspect/#remote-debugging no seu Chrome e " +
      "ative o remote debugging (Chrome 144+, uma vez). " +
      (hasPortFile
        ? "O arquivo DevToolsActivePort existe mas o WebSocket nao respondeu; " +
          "confirme que o seu Chrome esta aberto."
        : "Nao existe DevToolsActivePort no profile padrao."),
  );
}

export async function server(input: PluginInput): Promise<Hooks> {
  return {
    "tool.execute.before": async ({ tool }) => {
      if (tool === "chrome-devtools" || tool === "browser_navigate" || tool === "browser_*") {
        await ensureChromeDebug();
      }
    },
  };
}

export default {
  id: "llmfoundry-chrome-guarantee",
  server,
};
