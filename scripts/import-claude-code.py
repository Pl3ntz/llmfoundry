#!/usr/bin/env python3
"""import-claude-code.py: import Claude Code memories into LLMFoundry memory.

Imports the curated memory files from a Claude Code project (~/.claude/projects/
<project>/memory/*.md) into the local LLMFoundry memory engine.

Rules (validated in plan review):
- INSERT direct (not via remember()) so created_at preserves real chronology.
- Parser dual-structure: type comes from metadata.type OR filename prefix.
- Semantic mapping: feedback -> dynamic fact; project/reference/learning -> memories.
- Preserve origin in metadata JSON (originSessionId, type, modified).
- Dedup by content hash.
- Pre-scan secrets; log everything discarded, never silent.
- Writes ONLY to ~/.local/share/llmfoundry/memory/. Never touches the repo.

Usage:
    import-claude-code.py <claude_project_dir> [--project-name NAME]
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory"))
import foundry_memory as fm  # noqa: E402

# Semantic mapping from Claude Code memory types to LLMFoundry.
# All go to `memories` (full content, no truncation). Facts truncate at 1000
# chars and drop work rules, so feedback is never a fact.
TYPE_TO_MEMORY_TYPE = {
    "feedback": ("reference", "memories"),
    "project": ("reference", "memories"),
    "reference": ("reference", "memories"),
    "learning": ("reference", "memories"),
    "memory": ("reference", "memories"),
}

FILENAME_PREFIX_TYPE = {
    "feedback": "feedback",
    "project": "project",
    "reference": "reference",
    "learning": "learning",
}


def parse_frontmatter(text):
    """Return (frontmatter_dict, body). Supports both type locations."""
    fm_data = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            import yaml

            try:
                fm_data = yaml.safe_load(parts[1]) or {}
            except Exception:
                fm_data = {}
            body = parts[2]
    return fm_data, body


def get_type(fm_data, filename):
    """Type from metadata.type, top-level type, or filename prefix."""
    meta = fm_data.get("metadata") or {}
    t = meta.get("type") or fm_data.get("type")
    if t:
        return str(t).lower()
    for prefix, t in FILENAME_PREFIX_TYPE.items():
        if filename.startswith(prefix + "_"):
            return t
    return "memory"


def get_created_at(fm_data, filepath):
    """created_at from metadata.modified, else file mtime."""
    meta = fm_data.get("metadata") or {}
    modified = meta.get("modified")
    if modified:
        try:
            dt = datetime.fromisoformat(str(modified).replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        except Exception:
            pass
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def content_hash(content):
    return hashlib.sha256(content.strip().lower().encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("claude_project_dir", help="path to the Claude Code project memory dir")
    ap.add_argument("--project-name", default=None, help="container name (default: derived)")
    args = ap.parse_args()

    memory_dir = os.path.join(args.claude_project_dir, "memory")
    if not os.path.isdir(memory_dir):
        print(f"ERROR: no memory dir at {memory_dir}")
        return 1

    project = args.project_name or os.path.basename(args.claude_project_dir)
    # normalize the claude project dir name to something clean
    project = re.sub(r"^-Users-vplentz-dev-personal-", "", project)
    project = re.sub(r"^-[Uu]sers-vplentz-dev-", "", project)

    fm._conn()  # ensure schema
    seen_hashes = set()
    imported_facts = 0
    imported_memories = 0
    skipped_dup = 0
    skipped_secret = 0
    errors = 0
    con = fm._conn()

    files = sorted(f for f in os.listdir(memory_dir) if f.endswith(".md"))
    files = [f for f in files if f != "MEMORY.md"]  # index file, not a memory
    for fname in files:
        path = os.path.join(memory_dir, fname)
        try:
            raw = open(path).read()
        except Exception as e:
            errors += 1
            print(f"  [ERR] read {fname}: {e}")
            continue

        fm_data, body = parse_frontmatter(raw)
        if not body.strip():
            continue

        mem_type = get_type(fm_data, fname)
        created = get_created_at(fm_data, path)
        h = content_hash(body)

        if h in seen_hashes:
            skipped_dup += 1
            continue
        seen_hashes.add(h)

        # Idempotent: skip if this source file is already indexed for this container.
        # Checks the DB, not just this run, so re-importing does not duplicate.
        already = con.execute(
            "SELECT 1 FROM memories WHERE container=? AND metadata LIKE ? LIMIT 1",
            (project, f'%"source": "{fname}"%'),
        ).fetchone()
        if already:
            skipped_dup += 1
            continue

        # secret pre-scan
        if fm._blocked(body) or fm._blocked(fname):
            skipped_secret += 1
            print(f"  [SKIP secret] {fname}")
            continue

        mapped_type, target = TYPE_TO_MEMORY_TYPE.get(mem_type, ("reference", "memories"))
        origin = (fm_data.get("metadata") or {}).get("originSessionId", "")
        metadata = json.dumps({"type": mem_type, "originSessionId": origin, "source": fname})

        if target == "memory_facts":
            con.execute(
                """INSERT OR IGNORE INTO memory_facts
                   (container, fact_type, fact_text, confidence, reinforced_count, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (project, "dynamic", body.strip()[:1000], 1.0, 1, created, created),
            )
            imported_facts += 1
        else:
            con.execute(
                """INSERT INTO memories
                   (content, container, memory_type, project, session_id, metadata,
                    confidence, reinforced_count, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (body.strip(), project, mapped_type, project, origin or None, metadata,
                 1.0, 1, created, created),
            )
            imported_memories += 1
        con.commit()

    con.close()
    print(f"\n=== Import {project} complete ===")
    print(f"files found: {len(files)}")
    print(f"imported facts: {imported_facts}")
    print(f"imported memories: {imported_memories}")
    print(f"skipped duplicates: {skipped_dup}")
    print(f"skipped secrets: {skipped_secret}")
    print(f"errors: {errors}")
    print(f"DB: {fm.DB_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
