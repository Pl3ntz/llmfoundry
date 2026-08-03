import type { Hooks, PluginInput } from "@opencode-ai/plugin";

/**
 * LLMFoundry publish-guard — the output quality gate.
 *
 * Problem: voice-guard and verify-guard only scan file output (write/edit).
 * Chat output (emails, posts, messages, analysis) went unprotected. This
 * plugin closes that gap by injecting a mandatory verification instruction
 * into every system prompt via code. The model cannot forget it because the
 * injection is deterministic, not a skill it might miss.
 *
 * Philosophy: "code annotates, prompt judges." The code layer guarantees
 * the instruction is present. The model applies judgment (what's a false
 * positive? is this prose or code?). The code does not block.
 *
 * Injected gate (runs before every model turn):
 *   human-voice: dash detection, banlist vocabulary, rote transitions
 *   anti-delirium: conjecture-as-grounding, missing confidence markers
 *   ai-engineering-standards: preamble/closing filler, hedging
 *
 * Distilled from 3 skill files to fit in <300 tokens — the model carries
 * the full skills in context; this is the enforcement trigger.
 */

const PUBLISH_GATE = `
Before delivering any prose output (email, post, message, analysis, docs),
run this gate internally:

1. [human-voice] Scan for: em/en dashes (replace with periods/commas), AI
   banlist words (delve/leverage/foster/landscape/navigate/seamless/
   comprehensive/cutting-edge/state-of-the-art/unlock/empower/harness/
   streamline/pivotal/robust/furthermore/moreover/in conclusion/ultimately),
   rote transitions (first let me/in summary/to summarize/finally let),
   stacked compound hyphens (production-ready, well-documented).
2. [anti-delirium] Scan for conjecture-as-grounding: probably/should be/
   likely/seems/appears to be/i assume/i believe/as far as i know/must be.
   Every factual claim carries [VERIFIED], file:line, URL, or [UNVERIFIED].
3. [standards] No preamble ("Sure, let me..."). No closing filler ("In
   summary..."). First line IS the content. No hedging when you know the
   answer. Staff-engineer voice, not tutor.

If any check triggers: REWRITE before delivering. Do not ship flagged text.
If the text is code or a single-fact lookup, skip this gate.

This is not optional. The publish-guard plugin injects this instruction on
every turn. You cannot forget it.`
  .replace(/\n/g, " ")
  .replace(/\s{2,}/g, " ")
  .trim();

export async function server(_input: PluginInput): Promise<Hooks> {
  return {
    "experimental.chat.system.transform": async (_input, output) => {
      // Inject the publish gate into every system prompt. The model
      // carries the full skill definitions in context; this is the
      // enforcement trigger that can't be truncated away.
      output.system.push(PUBLISH_GATE);
    },
  };
}

export default {
  id: "llmfoundry-publish-guard",
  server,
};
