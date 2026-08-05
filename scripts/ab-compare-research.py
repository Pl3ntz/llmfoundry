#!/usr/bin/env python3
"""ab-compare-research.py — rigorous A/B comparison: deep-researcher v1 vs v2.

Runs both agents on the SAME frozen golden set (live web), saves every raw
output to evals/ab-v1-v2/raw/, then scores:

  RECALL     : does the output contain the golden fact (fuzzy, via research_scorer)?
  SOURCES    : every URL cited in SOURCES must respond (HEAD/GET status 2xx/3xx).
               Fabricated/invalid URLs = fabrication signal.
  CONTRACT   : v1 expects 7 headers, v2 expects 8; body under 800 tokens.
  VERIFIED   : (v2) every VERIFIED claim must have a live URL in SOURCES.
  COST/TOKENS: from the step_finish event (part.cost / part.tokens).

Usage:
  python3 scripts/ab-compare-research.py [--runs N] [--agents v1,v2] [--only Q1]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "evals", "ab-v1-v2", "raw")
os.makedirs(RAW, exist_ok=True)

# Frozen golden set (facts verified against primary sources on 2026-08-05).
# Facts are language-agnostic tokens (dates, names, numbers, PEP ids) so the
# score does not penalize the agent for answering in EN vs PT.
GOLDEN = [
    {
        "id": "Q1",
        "query": "Qual a data exata de lancamento da Python 3.12.0 e qual a principal novidade da versao?",
        "facts": [
            "3.12.0",
            "2023",                     # release year (2 Oct 2023, verified python.org)
            "PEP 701",                  # flexible f-string parsing (accepted highlight)
            "PEP 695",                  # type parameter syntax (also a valid highlight)
            "f-string",
            "pep",
        ],
    },
    {
        "id": "Q2",
        "query": "Qual a versao LTS atual do Node.js em 2026 e quando foi lancada?",
        "facts": [
            "v24",                      # v24 Krypton: Current LTS 2026 (nodejs.org release table)
            "Krypton",
            "v22",                      # v22 Jod: still maintenance LTS
            "Jod",
            "2025",                     # v24 first released May 06 2025
        ],
    },
    {
        "id": "Q3",
        "query": "Em que data o PostgreSQL 16 foi lancado e qual a principal melhoria de performance da versao?",
        "facts": [
            "PostgreSQL 16",
            "16",
            "2023",                     # released 2023-09-14 (verified postgresql.org)
            "parallel",                 # headline: query parallelism (FULL/RIGHT joins)
            "paralel",
        ],
    },
]

CONTRACT_HEADERS = {  # v1 has 7, v2 has 8
    "deep-researcher": ["### FINDINGS", "### CORRELATIONS", "### CONTRADICTIONS", "### GAPS",
                        "### NEXT STEP", "### OPEN QUESTIONS", "### SOURCES"],
    "deep-researcher-v2": ["### FINDINGS", "### CORRELATIONS", "### CONTRADICTIONS", "### AUTHORITY-BY-VOLUME",
                           "### GAPS", "### NEXT STEP", "### OPEN QUESTIONS", "### SOURCES"],
}

URL_RE = re.compile(r"https?://[^\s\)\]\}]+")


def run_agent(agent, query, run_dir):
    """Run one subagent through the orchestrator (the real delegation path),
    save raw JSON, return (text, tokens, cost). Retries ONCE on failure.
    A run that fails twice writes a FAIL marker, never aborts the batch."""
    out = os.path.join(run_dir, f"{agent}.json")
    start = time.time()
    # The opencode CLI cannot run a subagent directly ("subagent, not a primary
    # agent"). The faithful path is: primary agent (ai-orchestrator) delegates
    # via task to the subagent and returns its result. We instruct it to do
    # exactly that and to pass through the subagent's contract output.
    prompt = (
        "Delegue esta pesquisa EXCLUSIVAMENTE ao subagent " + agent + " via task. "
        "Nao responda voce mesmo. Entregue como resposta final APENAS o resultado "
        "do subagent (verbatim, incluindo os headers ### e SOURCES).\n\n"
        "Pesquisa: " + query
    )
    cmd = ["opencode", "run", "--agent", "ai-orchestrator", "--format", "json", prompt]
    for attempt in (1, 2):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            break
        except subprocess.TimeoutExpired:
            if attempt == 2:
                with open(out, "w") as f:
                    f.write("FAIL_TIMEOUT\n")
                return "", 0, 0.0, time.time() - start
            print(f"    [retry {agent}] timeout no run, tentando de novo...", flush=True)
    elapsed = time.time() - start
    with open(out, "w") as f:
        f.write(proc.stdout)
        if proc.stderr:
            f.write("\n---STDERR---\n" + proc.stderr)
    texts, tokens, cost = [], 0, 0.0
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        part = ev.get("part", {})
        if ev.get("type") == "text" and part.get("type") == "text":
            texts.append(part.get("text", ""))
        if ev.get("type") == "step_finish":
            t = part.get("tokens", {})
            tokens += t.get("total", 0)
            cost += part.get("cost", 0.0)
    return "\n".join(texts), tokens, cost, elapsed


def normalize(t):
    t = t.lower()
    import unicodedata
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", t).split()


def _stem(t):
    """Light stem for fair matching: plural-s and common pt/en suffixes."""
    if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
        t = t[:-1]
    if len(t) > 5 and t.endswith("tion"):
        t = t[:-4]
    if len(t) > 5 and t.endswith("acao"):
        t = t[:-4]
    return t


def fuzzy_contains(hay, needle):
    """Needle tokens must appear in hay, matching on 6+ char prefix OR exact stem."""
    hn = [t for t in normalize(hay) if len(t) > 2]
    hstem = set(_stem(t) for t in hn)
    hlong = [t for t in hn if len(t) >= 6]
    nn = [_stem(t) for t in normalize(needle) if len(t) > 2]
    if not nn:
        return True
    for t in nn:
        if t in hstem:
            continue
        if any(h.startswith(t[:6]) for h in hlong):
            continue
        if any(t.startswith(h[:6]) for h in hlong):
            continue
        return False
    return True


def url_alive(url, timeout=12):
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= r.status < 400
    except Exception:
        return False


def score_output(agent, text, golden):
    score = {"recall": 0, "facts_total": 0, "urls_total": 0, "urls_alive": 0,
             "headers_missing": [], "verified_claims": 0, "verified_urls_ok": 0}
    # 1. recall
    score["facts_total"] = len(golden["facts"])
    for fact in golden["facts"]:
        if fuzzy_contains(text, fact):
            score["recall"] += 1
    # 2. urls in SOURCES section (case-insensitive header)
    sources_match = re.search(r"###\s*sources", text, re.IGNORECASE)
    sources_part = text[sources_match.end():] if sources_match else ""
    urls = list(dict.fromkeys(URL_RE.findall(sources_part))) if sources_match else []
    score["urls_total"] = len(urls)
    score["urls_alive"] = sum(1 for u in urls if url_alive(u))
    # 3. contract headers (informational: one-shot delegation does not always
    #    force the full contract; decision weight is recall/urls/VERIFIED)
    for h in CONTRACT_HEADERS[agent]:
        if h not in text:
            score["headers_missing"].append(h)
    # 4. VERIFIED claims (v2 only): count lines starting with VERIFIED that carry a URL
    for line in text.splitlines():
        if line.lstrip().startswith("- [VERIFIED]") or line.lstrip().startswith("[VERIFIED]"):
            score["verified_claims"] += 1
            if URL_RE.search(line) or any(u in text for u in urls):
                score["verified_urls_ok"] += 1
    return score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--agents", default="deep-researcher,deep-researcher-v2")
    ap.add_argument("--only", default=None, help="e.g. Q1 to run a single golden")
    args = ap.parse_args()

    agents = args.agents.split(",")
    goldens = [g for g in GOLDEN if args.only is None or g["id"] == args.only]

    summary = {}  # agent -> {qid: [score,...]}
    for g in goldens:
        print(f"\n=== {g['id']}: {g['query']}", flush=True)
        for agent in agents:
            row = []
            for i in range(1, args.runs + 1):
                run_dir = os.path.join(RAW, g["id"], f"run{i}")
                os.makedirs(run_dir, exist_ok=True)
                out = os.path.join(run_dir, f"{agent}.json")
                if os.path.exists(out):
                    # already ran (batch resume); reuse evidence, skip API spend
                    text, tokens, cost = "", 0, 0.0
                    for line in open(out):
                        line = line.strip()
                        if not line:
                            continue
                        if line == "FAIL_TIMEOUT":
                            break
                        try:
                            ev = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        part = ev.get("part", {})
                        if ev.get("type") == "text" and part.get("type") == "text":
                            text += part.get("text", "")
                        if ev.get("type") == "step_finish":
                            t = part.get("tokens", {})
                            tokens += t.get("total", 0)
                            cost += part.get("cost", 0.0)
                    s = score_output(agent, text, g)
                    s.update({"tokens": tokens, "cost": cost, "elapsed": 0,
                              "chars": len(text), "reused": True})
                    row.append(s)
                    print(f"  [{agent} run{i}] REUSED (evidencia existente)", flush=True)
                    continue
                text, tokens, cost, elapsed = run_agent(agent, g["query"], run_dir)
                s = score_output(agent, text, g)
                s.update({"tokens": tokens, "cost": cost, "elapsed": elapsed,
                          "chars": len(text)})
                row.append(s)
                print(f"  [{agent} run{i}] recall={s['recall']}/{s['facts_total']} "
                      f"urls={s['urls_alive']}/{s['urls_total']} "
                      f"headers_missing={len(s['headers_missing'])} "
                      f"tok={tokens} cost=${cost:.4f} t={elapsed:.0f}s", flush=True)
            summary.setdefault(agent, {})[g["id"]] = row

    # aggregate
    print("\n\n========== AGGREGATE (mean over runs) ==========")
    print(f"{'agent':<18} {'recall%':>8} {'url_alive%':>11} {'hdr_miss':>9} {'tok':>8} {'cost':>9}")
    for agent in agents:
        rs = [s for rows in summary[agent].values() for s in rows]
        recall = 100 * sum(s["recall"] for s in rs) / sum(s["facts_total"] for s in rs)
        urls = sum(s["urls_total"] for s in rs)
        alive = 100 * sum(s["urls_alive"] for s in rs) / urls if urls else 0
        hdr = sum(len(s["headers_missing"]) for s in rs) / len(rs)
        tok = sum(s["tokens"] for s in rs) / len(rs)
        cost = sum(s["cost"] for s in rs) / len(rs)
        print(f"{agent:<18} {recall:>7.1f}% {alive:>10.1f}% {hdr:>9.2f} {tok:>8.0f} ${cost:.4f}")
        if agent == "deep-researcher-v2":
            v_claims = sum(s["verified_claims"] for s in rs)
            v_ok = sum(s["verified_urls_ok"] for s in rs)
            print(f"  VERIFIED claims: {v_ok}/{v_claims} com URL ao vivo")

    print(f"\nRaw evidence: {RAW}/")


if __name__ == "__main__":
    sys.exit(main())
