---
description: See and understand a visual, an image file, a screenshot, or the current screen. Routes to the vision-agent (vision model) which describes it in text for DeepSeek to act on.
model: opencode-go/deepseek-v4-pro
agent: ai-orchestrator
---

Analyze a visual and describe it for the executor.

**Target:** {{argument}}

The target is one of:
- An image FILE path (e.g. `~/Downloads/screen.png`) → read the file
- A screenshot already taken via chrome-devtools / screencapture → interpret it
- A URL of an image → fetch and describe
- The current screen / active window → capture it, then interpret

Flow:
1. If an image is attached or referenced, route to `vision-agent` (vision model)
2. Get the precise textual description (what is shown, elements, issues)
3. Return the description so DeepSeek can continue the task

Never try to read the image with a non-vision model. Output the description in the
vision-agent contract: IMAGE DESCRIPTION / NOTABLE ELEMENTS / ISSUES / ACTIONABLE SUMMARY.
