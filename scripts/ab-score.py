#!/usr/bin/env python3
"""ab-score.py: re-score ALL existing A/B evidence with the fixed matcher.

Reads evals/ab-v1-v2/raw/*/*/*.json (already saved), scores recall with a
prefix-tolerant matcher, checks URL liveness, counts VERIFIED claims.
No API spend: pure re-analysis of saved evidence.
"""
import json
import os
import re
import unicodedata
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "evals", "ab-v1-v2", "raw")

GOLDEN = {
    "Q1": ["3.12.0", "2023", "PEP 701", "PEP 695", "f-string", "pep"],
    "Q2": ["v24", "Krypton", "v22", "Jod", "2025"],
    "Q3": ["PostgreSQL 16", "16", "2023", "parallel", "paralel"],
}
URL_RE = re.compile(r"https?://[^\s\)\]\}]+")


def normalize(t):
    t = t.lower()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", t).split()


def _stem(t):
    if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
        t = t[:-1]
    if len(t) > 5 and t.endswith("tion"):
        t = t[:-4]
    if len(t) > 5 and t.endswith("acao"):
        t = t[:-4]
    return t


def fuzzy_contains(hay, needle):
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


def extract(fn):
    texts = []
    for line in open(fn):
        line = line.strip()
        if not line:
            continue
        if line.startswith("FAIL_TIMEOUT"):
            return ""
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        part = ev.get("part", {})
        if ev.get("type") == "text" and part.get("type") == "text":
            texts.append(part.get("text", ""))
    return "".join(texts)


def url_alive(u, timeout=10):
    try:
        req = urllib.request.Request(u, method="GET", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= r.status < 400
    except Exception:
        return False


def main():
    for qid, facts in GOLDEN.items():
        for agent in ["deep-researcher", "deep-researcher"]:
            recalls, url_ok, url_tot, verified = [], 0, 0, 0
            for run in range(1, 4):
                fn = os.path.join(RAW, qid, f"run{run}", f"{agent}.json")
                body = extract(fn)
                if not body:
                    recalls.append(0.0)
                    continue
                recall = sum(1 for f in facts if fuzzy_contains(body, f))
                recalls.append(recall / len(facts))
                sm = re.search(r"###\s*sources", body, re.I)
                urls = list(dict.fromkeys(URL_RE.findall(body[sm.end():]))) if sm else []
                url_tot += len(urls)
                url_ok += sum(1 for u in urls if url_alive(u))
                verified += sum(
                    1 for line in body.splitlines()
                    if line.lstrip().startswith(("[VERIFIED]", "- [VERIFIED]"))
                )
            print(f"{agent} {qid}: recall {[round(r, 2) for r in recalls]} "
                  f"media {sum(recalls)/len(recalls)*100:.1f}% "
                  f"urls {url_ok}/{url_tot} verified {verified}")

    print("\n=== MEDIA GERAL (9 runs por agent) ===")
    for agent in ["deep-researcher", "deep-researcher"]:
        allr = []
        ut = uo = vc = 0
        for qid, facts in GOLDEN.items():
            for run in range(1, 4):
                fn = os.path.join(RAW, qid, f"run{run}", f"{agent}.json")
                body = extract(fn)
                if body:
                    recall = sum(1 for f in facts if fuzzy_contains(body, f)) / len(facts)
                    allr.append(recall)
                sm = None
                if body:
                    sm = re.search(r"###\s*sources", body, re.I)
                urls = list(dict.fromkeys(URL_RE.findall(body[sm.end():]))) if sm and body else []
                ut += len(urls)
                uo += sum(1 for u in urls if url_alive(u))
                vc += sum(
                    1 for line in body.splitlines()
                    if line.lstrip().startswith(("[VERIFIED]", "- [VERIFIED]"))
                )
        print(f"{agent}: recall media {sum(allr)/len(allr)*100:.1f}% | "
              f"urls vivas {uo}/{ut} | VERIFIED claims {vc}")


if __name__ == "__main__":
    main()
