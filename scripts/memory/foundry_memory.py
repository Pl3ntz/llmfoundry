#!/usr/bin/env python3
"""foundry-memory — local-only memory engine for LLMFoundry.

Living feedback loop: agents/skills/commands feed it (encode) and consume it
(retrieve). Encode → Consolidate → Retrieve → Reconsolidate, like human memory.

Local-only. NEVER versioned. Data lives in ~/.local/share/llmfoundry/memory/.
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

DB_DIR = os.path.join(os.environ.get("HOME", os.path.expanduser("~")), ".local", "share", "llmfoundry", "memory")
DB_PATH = os.path.join(DB_DIR, "memory.db")
PROJECTS_DIR = os.path.join(DB_DIR, "projects")
EMBED_CACHE = os.path.join(os.environ.get("HOME", os.path.expanduser("~")), ".cache", "fastembed")

# Optional semantic layer (local ONNX embeddings via fastembed). Falls back to
# lexical-only (FTS5) if fastembed is not installed — graceful degradation.
EMBED_MODEL = os.environ.get("FOUNDRY_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
_semantic = None
_semantic_enabled = False


def _semantic_init():
    """Lazy-load fastembed. Returns True if semantic search is available."""
    global _semantic, _semantic_enabled
    if _semantic is not None:
        return _semantic_enabled
    try:
        from fastembed import TextEmbedding  # noqa: PLC0415

        _semantic = TextEmbedding(EMBED_MODEL, cache_dir=EMBED_CACHE)
        _semantic_enabled = True
    except Exception:
        _semantic = False
        _semantic_enabled = False
    return _semantic_enabled


def _embed(texts):
    """Embed a list of strings → list of float32 vectors. [] on failure."""
    if not _semantic_init():
        return []
    try:
        return [v.astype("float32") for v in _semantic.embed(list(texts))]
    except Exception:
        return []

# Decay: a memory not reinforced in this many days loses confidence.
DECAY_DAYS = 90
# Recall without action twice → stale.
STALE_RECALLS = 2
# Promotion: require this many recurrences (from the Promotion Criteria Matrix).
PROMOTE_THRESHOLD = 3

# Privacy: patterns we refuse to store locally (hard block).
_BLOCKED_PATTERNS = [
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\bAKIA[0-9A-Z]{16}\b",
    r"\bgh[pousr]_[A-Za-z0-9]{20,}\b",
    r"\bsk-[A-Za-z0-9]{20,}\b",
    r"\bAIza[0-9A-Za-z_-]{35}\b",
    r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.",
    r"(?i)\bsenha\b.{0,40}(=|:|\s+é\s+)\s*(?=[A-Za-z0-9_@#!$%&*+-]{8,}\S*)(?=.*\d|[^A-Za-z0-9])([A-Za-z0-9_@#!$%&*+-]{8,})",
    r"(?i)\b(password|passwd|pwd)\b.{0,40}(=|:)\s*\S+",
    r"(?i)\bapi[_-]?key\b.{0,40}(=|:)\s*\S+",
    r"(?i)\bsecret\b.{0,40}(=|:)\s*\S+",
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  content TEXT NOT NULL,
  container TEXT NOT NULL,
  memory_type TEXT NOT NULL DEFAULT 'event',
  project TEXT,
  session_id TEXT,
  metadata TEXT DEFAULT '{}',
  confidence REAL DEFAULT 1.0,
  reinforced_count INTEGER DEFAULT 1,
  last_reinforced_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_memories_container ON memories(container, memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
  content, project, content=memories, content_rowid=id, tokenize='porter unicode61'
);

CREATE TABLE IF NOT EXISTS memory_facts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  container TEXT NOT NULL,
  fact_type TEXT NOT NULL CHECK (fact_type IN ('static','dynamic','gotcha')),
  fact_text TEXT NOT NULL,
  confidence REAL DEFAULT 1.0,
  reinforced_count INTEGER DEFAULT 1,
  last_reinforced_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(container, fact_type, fact_text)
);
CREATE INDEX IF NOT EXISTS idx_facts_container ON memory_facts(container, fact_type);

CREATE TABLE IF NOT EXISTS gotchas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  container TEXT NOT NULL,
  pattern_hash TEXT NOT NULL,
  normalized_pattern TEXT NOT NULL,
  category TEXT DEFAULT 'general',
  count INTEGER DEFAULT 1,
  samples TEXT DEFAULT '[]',
  first_seen TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  last_seen TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  promoted INTEGER DEFAULT 0,
  UNIQUE(container, pattern_hash)
);
CREATE INDEX IF NOT EXISTS idx_gotchas_container ON gotchas(container, promoted);

CREATE TABLE IF NOT EXISTS findings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  container TEXT NOT NULL,
  agent_name TEXT NOT NULL,
  finding_text TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'MEDIUM' CHECK (severity IN ('CRITICAL','HIGH','MEDIUM','LOW','INFO')),
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved','superseded','wont_fix')),
  confidence REAL DEFAULT 1.0,
  recall_count INTEGER DEFAULT 0,
  reinforced_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(container, agent_name, finding_text)
);
CREATE INDEX IF NOT EXISTS idx_findings_container ON findings(container, status, severity);

CREATE TABLE IF NOT EXISTS recall_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  finding_id INTEGER,
  recalled_by TEXT NOT NULL,
  session_id TEXT,
  acted_on INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_recall_log ON recall_log(finding_id);

CREATE TABLE IF NOT EXISTS session_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  container TEXT NOT NULL,
  session_id TEXT NOT NULL UNIQUE,
  memories_captured INTEGER DEFAULT 0,
  findings_captured INTEGER DEFAULT 0,
  recalls INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- FTS triggers
CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
  INSERT INTO memories_fts(rowid, content, project) VALUES (new.id, new.content, new.project);
END;
CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
  INSERT INTO memories_fts(memories_fts, rowid, content, project) VALUES ('delete', old.id, old.content, old.project);
  INSERT INTO memories_fts(rowid, content, project) VALUES (new.id, new.content, new.project);
END;
CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
  INSERT INTO memories_fts(memories_fts, rowid, content, project) VALUES ('delete', old.id, old.content, old.project);
END;
"""


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%fZ")


def _conn():
    os.makedirs(DB_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(_SCHEMA)
    # idempotent migration: ensure session_id column on existing DBs
    try:
        con.execute("ALTER TABLE memories ADD COLUMN session_id TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    return con


def _hash(text):
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()[:16]


def _blocked(content):
    for p in _BLOCKED_PATTERNS:
        if re.search(p, content):
            return True
    return False


# ---------------- semantic vectors (local .npy, never versioned) ----------------

VEC_PATH = os.path.join(DB_DIR, "vectors.npz")


def _vec_load():
    """Load {memory_id: embedding} dict from the local .npz cache."""
    if not os.path.exists(VEC_PATH):
        return {}
    try:
        import numpy as np  # noqa: PLC0415

        data = np.load(VEC_PATH, allow_pickle=False)
        ids = data["ids"].tolist()
        vecs = data["vecs"]
        return dict(zip(ids, vecs))
    except Exception:
        return {}


def _vec_save(cache):
    """Persist {memory_id: embedding} to the local .npz cache."""
    if not cache:
        return
    try:
        import numpy as np  # noqa: PLC0415

        os.makedirs(os.path.dirname(VEC_PATH), exist_ok=True)
        ids = np.array(list(cache.keys()), dtype=np.int64)
        vecs = np.stack(list(cache.values())) if len(cache) > 1 else list(cache.values())[0].reshape(1, -1)
        np.savez(VEC_PATH, ids=ids, vecs=vecs)
    except Exception:
        pass


def _vec_upsert(memory_id, content):
    """Embed a memory and cache its vector. Best-effort."""
    if not _semantic_init():
        return
    vecs = _embed([content])
    if not vecs:
        return
    cache = _vec_load()
    cache[memory_id] = vecs[0]
    _vec_save(cache)


def _semantic_search(query, container=None, limit=10):
    """Vector search by cosine similarity. Returns [(memory_row, score)]."""
    if not _semantic_init():
        return []
    qvecs = _embed([query])
    if not qvecs:
        return []
    qv = qvecs[0]
    cache = _vec_load()
    if not cache:
        return []
    try:
        import numpy as np  # noqa: PLC0415

        ids = np.array(list(cache.keys()), dtype=np.int64)
        mat = np.stack(list(cache.values()))
        q = qv / (np.linalg.norm(qv) + 1e-9)
        mat = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9)
        scores = mat @ q
        order = np.argsort(-scores)[:limit]
        con = _conn()
        try:
            results = []
            for idx in order:
                row = con.execute("SELECT * FROM memories WHERE id=?", (int(ids[idx]),)).fetchone()
                if row and (container is None or row["container"] == container):
                    results.append((dict(row), float(scores[idx])))
            return results
        finally:
            con.close()
    except Exception:
        return []


# ---------------------------------------------------------------- encode

def remember(content, container="default", memory_type="event", project=None, session_id=None, metadata=None):
    """Store a structured memory linked to its opencode session. Returns id or None if blocked."""
    if _blocked(content):
        print("blocked: content contains a secret/PII pattern; not stored")
        return None
    con = _conn()
    try:
        cur = con.execute(
            "INSERT INTO memories (content, container, memory_type, project, session_id, metadata) VALUES (?,?,?,?,?,?)",
            (content, container, memory_type, project, session_id, json.dumps(metadata or {})),
        )
        con.commit()
        mid = cur.lastrowid
        # auto-embed for semantic recall (best-effort, local, non-blocking)
        _vec_upsert(mid, content)
        return mid
    finally:
        con.close()


def remember_fact(container, fact_type, fact_text):
    """Store/reinforce a profile fact. Dedup by (container, type, text)."""
    if _blocked(fact_text):
        print("blocked: fact contains a secret/PII pattern; not stored")
        return None
    con = _conn()
    try:
        con.execute(
            """INSERT INTO memory_facts (container, fact_type, fact_text)
               VALUES (?,?,?)
               ON CONFLICT(container, fact_type, fact_text) DO UPDATE SET
                 reinforced_count = reinforced_count + 1,
                 confidence = MIN(1.0, confidence + 0.1),
                 last_reinforced_at = ?""",
            (container, fact_type, fact_text, _now()),
        )
        con.commit()
        row = con.execute(
            "SELECT id FROM memory_facts WHERE container=? AND fact_type=? AND fact_text=?",
            (container, fact_type, fact_text),
        ).fetchone()
        return row["id"]
    finally:
        con.close()


def record_gotcha(container, pattern, category="general", sample=""):
    """Record/reinforce a recurring error pattern by hash."""
    if _blocked(pattern):
        print("blocked: gotcha contains a secret/PII pattern; not stored")
        return None
    ph = _hash(pattern)
    con = _conn()
    try:
        con.execute(
            """INSERT INTO gotchas (container, pattern_hash, normalized_pattern, category, samples)
               VALUES (?,?,?,?,?)
               ON CONFLICT(container, pattern_hash) DO UPDATE SET
                 count = count + 1,
                 last_seen = ?,
                 samples = ?""",
            (container, ph, pattern, category, json.dumps([sample] if sample else []), _now(),
             json.dumps([sample])),
        )
        con.commit()
        row = con.execute(
            "SELECT id, count FROM gotchas WHERE container=? AND pattern_hash=?", (container, ph)
        ).fetchone()
        return row["id"], row["count"]
    finally:
        con.close()


def record_finding(container, agent_name, finding_text, severity="MEDIUM"):
    """Record an agent finding. Returns (id, recall_count) on insert, (id, count) on reinforce."""
    if _blocked(finding_text):
        print("blocked: finding contains a secret/PII pattern; not stored")
        return None
    con = _conn()
    try:
        con.execute(
            """INSERT INTO findings (container, agent_name, finding_text, severity)
               VALUES (?,?,?,?)
               ON CONFLICT(container, agent_name, finding_text) DO UPDATE SET
                 recall_count = recall_count + 1,
                 updated_at = ?""",
            (container, agent_name, finding_text, severity, _now()),
        )
        con.commit()
        row = con.execute(
            "SELECT id, recall_count FROM findings WHERE container=? AND agent_name=? AND finding_text=?",
            (container, agent_name, finding_text),
        ).fetchone()
        return row["id"], row["recall_count"]
    finally:
        con.close()


# ---------------------------------------------------------------- retrieve

def search(query, container=None, limit=10):
    """Hybrid search: FTS5 (lexical) + embeddings (semantic), merged by rank.

    Falls back to lexical-only if fastembed isn't available. Semantic enriches
    recall for agents: a question like "which model is cheapest" finds a memory
    about choosing DeepSeek over kimi-k3 even without shared tokens.
    """
    # Lexical results (always)
    con = _conn()
    lexical = {}
    try:
        if container:
            rows = con.execute(
                """SELECT m.* FROM memories m
                   JOIN memories_fts f ON f.rowid = m.id
                   WHERE memories_fts MATCH ? AND m.container = ?
                   ORDER BY bm25(memories_fts) LIMIT ?""",
                (query, container, limit),
            ).fetchall()
        else:
            rows = con.execute(
                """SELECT m.* FROM memories m
                   JOIN memories_fts f ON f.rowid = m.id
                   WHERE memories_fts MATCH ?
                   ORDER BY bm25(memories_fts) LIMIT ?""",
                (query, limit),
            ).fetchall()
        for i, r in enumerate(rows):
            lexical[r["id"]] = {"row": dict(r), "rank": i}
    finally:
        con.close()

    # Semantic results (if available)
    semantic_rows = _semantic_search(query, container, limit)
    merged = {}
    for item, _score in semantic_rows:
        if item["id"] not in merged:
            merged[item["id"]] = {"row": item, "rank": len(merged)}

    # Merge: lexical wins ties, semantic fills gaps, dedup by id
    out = []
    seen = set()
    for pool in (lexical, merged):
        for mid in sorted(pool, key=lambda k: pool[k]["rank"]):
            if mid in seen:
                continue
            seen.add(mid)
            out.append(pool[mid]["row"])
            if len(out) >= limit:
                return out
    return out


def recall(container=None, top=5, project=None):
    """Recall the most relevant context for a preamble.

    Returns open findings, recent gotchas, AND the most relevant memories and
    facts of the container, so imported knowledge enters agent context
    automatically instead of only via explicit search.

    Quando `project` e passado (estilo Claude Code), memories/facts buscam as
    do projeto MAIS as globais (project NULL ou 'default'), deduplicadas e com
    prioridade para as do projeto. Gotchas e findings permanecem por container:
    sao padroes tecnicos transversais, nao conhecimento de projeto.
    """
    con = _conn()
    try:
        where = "WHERE status='open'" + (" AND container=?" if container else "")
        params = (container,) if container else ()
        findings = con.execute(
            f"SELECT * FROM findings {where} ORDER BY recall_count ASC, created_at DESC LIMIT ?",
            params + (top,),
        ).fetchall()
        gw = "WHERE promoted=0" + (" AND container=?" if container else "")
        gotchas = con.execute(
            f"SELECT * FROM gotchas {gw} ORDER BY count DESC LIMIT ?", params + (top,)
        ).fetchall()
        if project:
            # memórias: do projeto primeiro, globais em segundo. Dedup por id,
            # e o projeto sempre ganha a vaga se empatar com uma global.
            # container opcional: sem container, busca em todos; com, filtra.
            if container:
                mw = (
                    "WHERE 1=1 AND container=?"
                    " AND (project=? OR project IS NULL OR project='default')"
                )
                memories = con.execute(
                    f"SELECT * FROM memories {mw} "
                    "ORDER BY CASE WHEN project=? THEN 0 ELSE 1 END, "
                    "confidence DESC, reinforced_count DESC, created_at DESC LIMIT ?",
                    (container, project, project, top),
                ).fetchall()
            else:
                mw = "WHERE 1=1 AND (project=? OR project IS NULL OR project='default')"
                memories = con.execute(
                    f"SELECT * FROM memories {mw} "
                    "ORDER BY CASE WHEN project=? THEN 0 ELSE 1 END, "
                    "confidence DESC, reinforced_count DESC, created_at DESC LIMIT ?",
                    (project, project, top),
                ).fetchall()
            # facts sao perfil transversal (nao tem coluna project): ficam por
            # container, como o CLAUDE.md global do Claude Code.
            fw = "WHERE 1=1" + (" AND container=?" if container else "")
            facts = con.execute(
                f"SELECT * FROM memory_facts {fw} ORDER BY reinforced_count DESC, confidence DESC, created_at DESC LIMIT ?",
                params + (top,),
            ).fetchall()
        else:
            mw = "WHERE 1=1" + (" AND container=?" if container else "")
            memories = con.execute(
                f"SELECT * FROM memories {mw} ORDER BY confidence DESC, reinforced_count DESC, created_at DESC LIMIT ?",
                params + (top,),
            ).fetchall()
            fw = "WHERE 1=1" + (" AND container=?" if container else "")
            facts = con.execute(
                f"SELECT * FROM memory_facts {fw} ORDER BY reinforced_count DESC, confidence DESC, created_at DESC LIMIT ?",
                params + (top,),
            ).fetchall()
        return {
            "findings": [dict(r) for r in findings],
            "gotchas": [dict(r) for r in gotchas],
            "memories": [dict(r) for r in memories],
            "facts": [dict(r) for r in facts],
        }
    finally:
        con.close()


def log_recall(container, recalled_by, session_id=None, acted_on=False):
    """Log a recall event. If an open finding is recalled 2x without action → flag stale."""
    con = _conn()
    try:
        finding = con.execute(
            "SELECT id FROM findings WHERE container=? AND status='open' ORDER BY recall_count DESC LIMIT 1",
            (container,),
        ).fetchone()
        if finding:
            con.execute(
                "INSERT INTO recall_log (finding_id, recalled_by, session_id, acted_on) VALUES (?,?,?,?)",
                (finding["id"], recalled_by, session_id, 1 if acted_on else 0),
            )
            if not acted_on:
                con.execute(
                    "UPDATE findings SET recall_count = recall_count + 1 WHERE id=?",
                    (finding["id"],),
                )
            con.commit()
            # stale check
            row = con.execute("SELECT recall_count FROM findings WHERE id=?", (finding["id"],)).fetchone()
            return row["recall_count"]
        return 0
    finally:
        con.close()


# ---------------------------------------------------------------- consolidate

def apply_decay():
    """Decay confidence of memories/facts not reinforced in DECAY_DAYS."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=DECAY_DAYS)).strftime("%Y-%m-%dT%H:%M:%fZ")
    con = _conn()
    try:
        cur = con.execute(
            "UPDATE memory_facts SET confidence = MAX(0.1, confidence - 0.2), updated_at=? WHERE last_reinforced_at < ?",
            (_now(), cutoff),
        )
        con.commit()
        return cur.rowcount
    finally:
        con.close()


def promote(container, dry_run=False):
    """Promote gotchas with count >= PROMOTE_THRESHOLD to the curated local layer."""
    con = _conn()
    try:
        rows = con.execute(
            "SELECT * FROM gotchas WHERE container=? AND count >= ? AND promoted=0",
            (container, PROMOTE_THRESHOLD),
        ).fetchall()
        if dry_run:
            return [dict(r) for r in rows]
        os.makedirs(PROJECTS_DIR, exist_ok=True)
        gotchas_path = os.path.join(PROJECTS_DIR, container, "GOTCHAS.md")
        os.makedirs(os.path.dirname(gotchas_path), exist_ok=True)
        lines = ["# GOTCHAS — local (never committed)", ""]
        changed = 0
        for r in rows:
            lines.append(f"- **{r['normalized_pattern']}** (x{r['count']}, {r['category']})")
            con.execute("UPDATE gotchas SET promoted=1 WHERE id=?", (r["id"],))
            changed += 1
        if changed:
            with open(gotchas_path, "w") as f:
                f.write("\n".join(lines) + "\n")
            con.commit()
            print(f"promoted {changed} gotchas → {gotchas_path}")
        return changed
    finally:
        con.close()


def stats(container=None):
    con = _conn()
    try:
        w = "WHERE container=?" if container else ""
        p = (container,) if container else ()
        w_open = "WHERE container=? AND status='open'" if container else "WHERE status='open'"
        memories = con.execute(f"SELECT COUNT(*) c FROM memories {w}", p).fetchone()["c"]
        facts = con.execute(f"SELECT COUNT(*) c FROM memory_facts {w}", p).fetchone()["c"]
        gotchas = con.execute(f"SELECT COUNT(*) c FROM gotchas {w}", p).fetchone()["c"]
        findings = con.execute(f"SELECT COUNT(*) c FROM findings {w}", p).fetchone()["c"]
        open_findings = con.execute(f"SELECT COUNT(*) c FROM findings {w_open}", p).fetchone()["c"]
        recalls = con.execute("SELECT COUNT(*) c FROM recall_log").fetchone()["c"]
        acted = con.execute("SELECT COUNT(*) c FROM recall_log WHERE acted_on=1").fetchone()["c"]
        return {
            "memories": memories, "facts": facts, "gotchas": gotchas,
            "findings": findings, "open_findings": open_findings,
            "recalls": recalls, "recalls_acted": acted,
        }
    finally:
        con.close()


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(prog="foundry-memory", description="LLMFoundry local memory")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("remember", help="store a memory")
    p.add_argument("content"); p.add_argument("--container", default="default")
    p.add_argument("--type", default="event"); p.add_argument("--project")

    p = sub.add_parser("fact", help="store/reinforce a profile fact")
    p.add_argument("container"); p.add_argument("fact_type", choices=["static","dynamic","gotcha"]); p.add_argument("fact_text")

    p = sub.add_parser("gotcha", help="record a recurring error pattern")
    p.add_argument("container"); p.add_argument("pattern"); p.add_argument("--category", default="general"); p.add_argument("--sample", default="")

    p = sub.add_parser("finding", help="record an agent finding")
    p.add_argument("container"); p.add_argument("agent"); p.add_argument("text"); p.add_argument("--severity", default="MEDIUM")

    p = sub.add_parser("search", help="full-text search")
    p.add_argument("query"); p.add_argument("--container"); p.add_argument("--limit", type=int, default=10)

    p = sub.add_parser("recall", help="recall open findings + gotchas for preamble")
    p.add_argument("--container"); p.add_argument("--top", type=int, default=5)
    p.add_argument("--project", help="nome do projeto/diretorio (estilo Claude Code): traz memories/facts do projeto + globais")

    p = sub.add_parser("log-recall", help="log a recall event")
    p.add_argument("--container", required=True); p.add_argument("--by", default="unknown")
    p.add_argument("--session"); p.add_argument("--acted", action="store_true")

    p = sub.add_parser("decay", help="apply temporal decay")
    p = sub.add_parser("promote", help="promote recurring gotchas to curated layer")
    p.add_argument("--container", required=True); p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("stats", help="memory stats"); p.add_argument("--container")

    args = ap.parse_args()

    if args.cmd == "remember":
        id_ = remember(args.content, args.container, args.type, args.project)
        print(f"stored id={id_}" if id_ else "not stored (blocked)")
    elif args.cmd == "fact":
        id_ = remember_fact(args.container, args.fact_type, args.fact_text)
        print(f"fact id={id_}" if id_ else "not stored (blocked)")
    elif args.cmd == "gotcha":
        r = record_gotcha(args.container, args.pattern, args.category, args.sample)
        if r: print(f"gotcha id={r[0]} count={r[1]}")
        else: print("not stored (blocked)")
    elif args.cmd == "finding":
        r = record_finding(args.container, args.agent, args.text, args.severity)
        if r: print(f"finding id={r[0]} recalls={r[1]}")
        else: print("not stored (blocked)")
    elif args.cmd == "search":
        for m in search(args.query, args.container, args.limit):
            print(f"[{m['id']}] [{m['memory_type']}] {m['content'][:120]}")
    elif args.cmd == "recall":
        data = recall(args.container, args.top, args.project)
        print("=== FINDINGS ===")
        for f in data["findings"]:
            sev = f["severity"]
            text = f["finding_text"]
            if not text.startswith("["):
                text = f"[{sev}] {text}"
            print(text[:120])
        print("=== GOTCHAS ===")
        for g in data["gotchas"]:
            print(f"(x{g['count']}) {g['normalized_pattern'][:120]}")
        print("=== MEMORIES ===")
        for m in data["memories"]:
            print(f"[{m['memory_type']}] {m['content'][:120]}")
        print("=== FACTS ===")
        for f in data["facts"]:
            print(f"[{f['fact_type']}] {f['fact_text'][:120]}")
    elif args.cmd == "log-recall":
        n = log_recall(args.container, args.by, args.session, args.acted)
        print(f"recall logged; finding recall_count={n}")
    elif args.cmd == "decay":
        print(f"decayed {apply_decay()} facts")
    elif args.cmd == "promote":
        promote(args.container, args.dry_run)
    elif args.cmd == "stats":
        s = stats(args.container)
        for k, v in s.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    sys.exit(main())
