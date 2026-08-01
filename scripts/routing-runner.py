#!/usr/bin/env python3
"""routing-runner.py — measure how well the orchestrator routes.

Runs each golden routing question through the orchestrator (headless opencode),
classifies the response into a route, and scores against the expected route.

Usage:
    routing-runner.py [--dry-run] [--limit N]
"""

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(ROOT, "evals", "orchestrator", "golden-set.json")
SCORER = os.path.join(ROOT, "scripts", "routing-score.py")

# Heuristic route classification from the orchestrator's response text.
def classify(text: str) -> str:
    t = text.lower()
    # Interview: asks a question one-at-a-time, no execution
    if re.search(r"primeira pergunta|primeira:|\bpergunta 1\b|uma de cada vez|onde está|me diz|me conta|qual o propósito|qual é o caso", t) and "?" in t:
        return "interview"
    # Deep research: structured findings + sources
    if "### sources" in t or "fontes:" in t or "### findings" in t or re.search(r"fontes? (trianguladas|independentes)", t):
        return "deep-researcher"
    # Security review: threat model / findings severity
    if re.search(r"### findings|\[(critical|high|medium|low)\]|owasp|prompt injection defense", t):
        return "llm-security-reviewer"
    # Architecture: trade-offs, decision matrix
    if re.search(r"decision matrix|trade-?offs|arquitetura|architecture", t) and re.search(r"option|alternativa|pros|cons", t):
        return "ai-architect"
    # Evals
    if re.search(r"eval|golden set|regressão|baseline", t) and re.search(r"test|cases|assert", t):
        return "ai-evals-runner"
    # Build/implementation
    if re.search(r"implement|build|código|implementation|vou criar", t) and re.search(r"spec|passo|step", t):
        return "build"
    # Default: direct answer
    return "direct"


def run_question(q: dict) -> dict:
    prompt = q["prompt"]
    cmd = ["opencode", "run", prompt, "--agent", "ai-orchestrator", "--auto"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=240, cwd=os.path.expanduser("~/dev/personal/opencode"))
        out = r.stdout or ""
        # strip ANSI
        out = re.sub(r"\x1b\[[0-9;]*m", "", out)
        route = classify(out)
        return {"id": q["id"], "expected": q["expectedRoute"], "actual": route, "output": out[:300]}
    except subprocess.TimeoutExpired:
        return {"id": q["id"], "expected": q["expectedRoute"], "actual": "timeout", "output": ""}
    except Exception as e:
        return {"id": q["id"], "expected": q["expectedRoute"], "actual": f"error:{e}", "output": ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=12)
    args = ap.parse_args()

    data = json.load(open(GOLDEN))
    questions = data["questions"][: args.limit]

    # import scorer
    import importlib.util

    spec = importlib.util.spec_from_file_location("rs", SCORER)
    rs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rs)

    results = []
    for q in questions:
        exp = {"expectedRoute": q["expectedRoute"], "expectedGates": q.get("expectedGates", {})}
        if args.dry_run:
            act = {"route": "unknown", "gates": {}}
            print(f"[dry] {q['id']} expected={q['expectedRoute']}")
            continue
        r = run_question(q)
        route = r["actual"]
        act = {"route": route, "gates": {}}
        rscore = rs._route_match(rs._route(exp), rs._route(act))
        gscore = rs._gate_score(rs._gates(exp), rs._gates(act))
        comp = rs.WEIGHTS["route-match"] * rscore + rs.WEIGHTS["gate-correctness"] * gscore
        ok = "PASS" if rscore >= 0.6 else "FAIL"
        results.append((r, rscore, comp))
        print(f"[{ok}] {r['id']} expected={r['expected']} actual={route} route_score={rscore:.2f} composite={comp:.2f}")

    if not args.dry_run and results:
        passed = sum(1 for _, s, _ in results if s >= 0.6)
        print(f"\nROUTING BASELINE: {passed}/{len(results)} correct ({passed/len(results)*100:.0f}%)")
        # save baseline
        baseline = {
            "version": 1, "captured": "2026-08-01",
            "suite": "routing-runner", "questions": len(results),
            "passed": passed, "percent": round(passed/len(results)*100),
            "results": [{"id": r["id"], "expected": r["expected"], "actual": r["actual"]} for r, _, _ in results],
        }
        with open(os.path.join(ROOT, "evals", "orchestrator", "baseline.json"), "w") as f:
            json.dump(baseline, f, indent=2)
        print(f"baseline saved: evals/orchestrator/baseline.json")


if __name__ == "__main__":
    sys.exit(main())
