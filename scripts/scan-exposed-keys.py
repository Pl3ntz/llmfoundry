#!/usr/bin/env python3
"""scan-exposed-keys.py — passive scan for HIGH-SEVERITY exposed API keys.

Finds public repos that commit real secrets in .env/config files: AWS AKIA,
Stripe sk_live, Firebase AIza, OpenAI sk-. Filters out documentation noise
(READMEs of regex tools, .example files). ONLY reads public data, NEVER uses
a found key. Output: candidates for responsible disclosure.

Usage:
    scan-exposed-keys.py [--pattern AKIA] [--limit 10] [--json]
"""

import argparse
import base64
import json
import re
import subprocess
import sys

# High-severity key patterns (real keys, not placeholders)
KEY_PATTERNS = {
    "AKIA": {
        "regex": re.compile(r"AKIA[0-9A-Z]{16}"),
        "severity": "HIGH",
        "label": "AWS Access Key",
        "query": "AKIA+in:path+.env",
    },
    "sk_live": {
        "regex": re.compile(r"sk_live_[0-9a-zA-Z]{16,}"),
        "severity": "HIGH",
        "label": "Stripe Secret Key",
        "query": "sk_live_+in:file",
    },
    "AIza": {
        "regex": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
        "severity": "MEDIUM",
        "label": "Google API Key",
        "query": "AIza+in:file+extension:json",
    },
    "sk-": {
        "regex": re.compile(r"sk-[A-Za-z0-9]{30,}"),
        "severity": "HIGH",
        "label": "OpenAI/Anthropic Key",
        "query": "sk-+in:file+extension:env",
    },
}

# Files that are documentation/tooling, not real exposure
NOISE_PATHS = (
    "README", "CLAUDE.md", "AGENTS.md", "USAGE.md", "SETUP", "DEPLOY",
    "regex", "RegeX", "secret-regex", "keyhacks", "Bug-Bounty", "llms.txt",
)
# Files that are examples, not real secrets
EXAMPLE_PATHS = (".example", ".sample", "_example", "-example", "EXAMPLE_")


def gh_api(path, jq=None):
    cmd = ["gh", "api", path]
    if jq:
        cmd += ["--jq", jq]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def gh_search_code(query, per_page=8):
    out = gh_api(f"search/code?q={query}&per_page={per_page}")
    if not out:
        return []
    try:
        return json.loads(out).get("items", [])
    except Exception:
        return []


def fetch_file(repo, path):
    out = gh_api(f"repos/{repo}/contents/{path}", jq=".content")
    if not out:
        return ""
    try:
        return base64.b64decode(out.strip()).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def is_noise(repo, path):
    upper = (repo + " " + path).upper()
    for n in NOISE_PATHS:
        if n.upper() in upper:
            return True
    for e in EXAMPLE_PATHS:
        if e in path.lower():
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", choices=list(KEY_PATTERNS), default="AKIA")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cfg = KEY_PATTERNS[args.pattern]
    print(f"=== Scanning for {cfg['label']} (severity: {cfg['severity']}) ===")
    print("(passive: only public data, never using a key)")
    print()

    items = gh_search_code(cfg["query"], per_page=args.limit * 3)
    results = []
    seen = set()

    for it in items:
        repo = it["repository"]["full_name"]
        path = it["path"]
        if is_noise(repo, path):
            continue
        url = it["html_url"]
        content = fetch_file(repo, path)
        matches = cfg["regex"].findall(content)
        if not matches:
            continue
        key = matches[0]
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "repo": repo, "path": path, "url": url,
            "key": key[:20] + "...", "severity": cfg["severity"], "type": cfg["label"],
        })
        if len(results) >= args.limit:
            break

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if not results:
            print("No real high-severity exposure found in this sample.")
            print("Tip: try --pattern sk_live or AIza for more surface.")
        for r in results:
            print(f"[{r['severity']}] {r['type']}")
            print(f"  repo: {r['repo']}")
            print(f"  file: {r['path']}")
            print(f"  url:  {r['url']}")
            print(f"  key:  {r['key']} (masked, never used)")
            print()


if __name__ == "__main__":
    sys.exit(main())
