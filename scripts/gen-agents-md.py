#!/usr/bin/env python3
"""gen-agents-md.py: generate a short AGENTS.md for a project from its imported memory.

Reads the LLMFoundry memory container for a project and writes a compact
AGENTS.md into the project directory, summarizing the top memories as context.
Local artifact, not part of the LLMFoundry repo.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory"))
import foundry_memory as fm  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("container", help="memory container name (the project)")
    ap.add_argument("project_dir", help="local project directory to write AGENTS.md into")
    ap.add_argument("--top", type=int, default=8)
    args = ap.parse_args()

    data = fm.recall(container=args.container, top=args.top)
    memories = data.get("memories", [])
    facts = data.get("facts", [])

    if not memories and not facts:
        print(f"no memory for container {args.container}, skipping")
        return

    lines = [f"# {args.container}", ""]
    lines.append("Project context imported from LLMFoundry memory (Claude Code sessions).")
    lines.append("")
    lines.append("## Context")
    lines.append("")
    for m in memories:
        snippet = " ".join(m["content"].split())[:250]
        lines.append(f"- {snippet}")
    if facts:
        lines.append("")
        lines.append("## Facts")
        lines.append("")
        for f in facts:
            snippet = " ".join(f["fact_text"].split())[:200]
            lines.append(f"- {snippet}")

    os.makedirs(args.project_dir, exist_ok=True)
    path = os.path.join(args.project_dir, "AGENTS.md")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {path} ({len(memories)} memories, {len(facts)} facts)")


if __name__ == "__main__":
    sys.exit(main())
