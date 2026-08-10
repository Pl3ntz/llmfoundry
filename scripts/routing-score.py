#!/usr/bin/env python3
"""routing-score.py: deterministic orchestrator routing eval scorer.

Compares a golden question (EXPECTED) against an orchestrator answer (ACTUAL),
both with {route, gates}. Route match wins on exact or acceptable alternative.
A REQUIRED gate being skipped is a HARD-FAIL regardless of route match.

Usage:
    routing-score.py EXPECTED.json ACTUAL.json [--json]
Exit 0 = pass, 1 = fail.
"""

import argparse
import json
import sys

WEIGHTS = {
    "route-match": 0.60,
    "gate-correctness": 0.40,
}
PASS_THRESHOLD = 0.70

# acceptable alternatives per expected route
ALTERNATIVES = {
    "deep-researcher": ["ai-research", "research"],
    "ai-architect": ["architect"],
    "ai-evals-runner": ["evals"],
    "llm-security-reviewer": ["security"],
    "direct": ["answer", "self"],
    "build": ["implementation", "orchestrator-direct"],
}


def _route(obj):
    return (obj.get("expectedRoute") or obj.get("route") or "").lower().strip()


def _gates(obj):
    return obj.get("expectedGates") or obj.get("gates") or {}


def _route_match(expected, actual):
    if actual == expected:
        return 1.0
    alts = ALTERNATIVES.get(expected, [])
    if actual in alts:
        return 1.0
    return 0.0


def _gate_score(expected_gates, actual_gates):
    """Each expected gate present in actual = pass. Missing required = fail."""
    if not expected_gates:
        return 1.0
    total = len(expected_gates)
    matched = 0
    for key, expected_val in expected_gates.items():
        actual_val = actual_gates.get(key)
        if actual_val == expected_val:
            matched += 1
    return matched / total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("expected")
    ap.add_argument("actual")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    expected = json.load(open(args.expected))
    actual = json.load(open(args.actual))

    exp_route = _route(expected)
    act_route = _route(actual)
    exp_gates = _gates(expected)
    act_gates = _gates(actual)

    route_score = _route_match(exp_route, act_route)
    gate_score = _gate_score(exp_gates, act_gates)

    composite = WEIGHTS["route-match"] * route_score + WEIGHTS["gate-correctness"] * gate_score
    passed = composite >= PASS_THRESHOLD

    result = {
        "expected_route": exp_route,
        "actual_route": act_route,
        "route_score": round(route_score, 3),
        "gate_score": round(gate_score, 3),
        "composite": round(composite, 3),
        "passed": passed,
    }
    if args.json:
        print(json.dumps(result))
    else:
        print(f"expected: {exp_route} | actual: {act_route}")
        print(f"route={route_score:.2f} gates={gate_score:.2f} composite={composite:.2f} {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
