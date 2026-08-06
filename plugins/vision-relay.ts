import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry vision-relay: makes pasted images work even when the main
 * model (DeepSeek V4) has no vision.
 *
 * Problem: when the Owner pastes an image in the TUI, the image part goes to
 * the main model (deepseek, no vision) which errors "model does not support
 * image input".
 *
 * Solution: intercept user messages in experimental.chat.messages.transform.
 * For every image part, save it to a temp file and insert a text instruction
 * telling the orchestrator to route the image to the vision-agent (kimi-k3,
 * the only Go-plan model with real vision). The text replaces the raw image
 * so the main model never has to parse pixels itself.
 */

import { execSync } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

const VISION_AGENT = "vision-agent";
const VISION_MODEL = "opencode-go/kimi-k3";

function isImagePart(part: any): boolean {
  if (!part || typeof part !== "object") return false;
  if (part.type === "image") return true;
  // some versions put it under mediaType or data with an image mime
  const mt = String(part.mediaType || part.mimeType || part.type || "");
  return /^image\//.test(mt) || mt === "image";
}

export async function server(input: PluginInput): Promise<Hooks> {
  return {
    "experimental.chat.messages.transform": async (_input, output) => {
      const { messages } = output;
      if (!messages) return;

      for (const msg of messages) {
        if (!msg.parts || msg.info?.role !== "user") continue;
        const newParts: any[] = [];
        let imageFound = false;

        for (const part of msg.parts) {
          if (isImagePart(part)) {
            imageFound = true;
            // Try to persist the image so the vision-agent can read the file.
            const data = part.data || part.image || part.content;
            if (typeof data === "string") {
              try {
                const ext = (part.mediaType || "image/png").split("/")[1] || "png";
                const file = path.join(
                  os.tmpdir(),
                  `llmfoundry-paste-${Date.now()}.${ext}`,
                );
                const base64 = data.replace(/^data:[^;]+;base64,/, "");
                fs.writeFileSync(file, Buffer.from(base64, "base64"));
                newParts.push({
                  type: "text",
                  text: `[image pasted, saved to ${file}]. Route to ${VISION_AGENT} (model ${VISION_MODEL}) to read this image and describe it. Do NOT try to read the image yourself, your model has no vision.`,
                });
              } catch (e) {
                newParts.push({
                  type: "text",
                  text: `[image pasted but could not be saved: ${String(e)}]. Ask the Owner for the image path and route to ${VISION_AGENT}.`,
                });
              }
            } else {
              newParts.push({
                type: "text",
                text: `[image pasted in non-file form]. Ask the Owner to save it as a file, then route to ${VISION_AGENT}.`,
              });
            }
          } else {
            newParts.push(part);
          }
        }

        if (imageFound) {
          msg.parts = newParts;
        }
      }
    },
  };
}

export default {
  id: "llmfoundry-vision-relay",
  server,
};
