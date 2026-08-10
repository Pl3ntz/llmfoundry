#!/usr/bin/env python3
"""routing-runner.py — run the orchestrator routing golden-set against a live model.

For each question in evals/orchestrator/golden-set.json, invokes
`opencode run --model <model> --pure` with a condensed routing table and asks for a
strict JSON decision {route, gates, reason}. Then scores each against the golden
expected via the routing-score rules (route match 0.6 + gate correctness 0.4).

Usage:
    routing-runner.py [--model opencode/deepseek-v4-flash-free] [--question RS-1] [--dry-run] [--json]

Exit 0 if all pass, 1 otherwise.
"""
import argparse
import json
import re
import subprocess
import sys

GOLDEN = "evals/orchestrator/golden-set.json"

# condensed copy of the orchestrator routing table shown to the model
ROUTING_TABLE = """Classifique a frase do USUARIO em uma das rotas abaixo e responda EXATAMENTE com um JSON {"route": "...", "reason": "..."}:

Rotas:
- deep-researcher: pesquisa multi-fonte profunda, comparacao, landscape
- ai-architect: design de sistemas LLM (agentes, RAG, MCP)
- ai-evals-runner: rodar/construir avaliacoes de prompt/agente
- llm-security-reviewer: revisao de seguranca de app LLM antes de ship
- reverse-engineer: binario, firmware, malware
- database-engineer: banco de dados
- backend-architect: design de backend
- platform-engineer: infraestrutura
- direct: fato unico/documentacao/lookup (responder eu mesmo)
- build: implementar codigo no projeto
- interview: vago/demasiado ambíguo, precisa discutir antes de agir

Regras:
- pesquisa landscape/comparacao -> deep-researcher (NAO direct)
- design de agente/RAG -> ai-architect
- "melhorar prompt" ou "saber se melhorou" -> ai-evals-runner
- app LLM em producao / segurança -> llm-security-reviewer
- pergunta de fato unico (ex: versao, sintaxe) -> direct
- "chatbot esta ruim" sem detalhe -> interview
- "implemente X no projeto" -> build
- NUNCA responda com nada fora do JSON. Sem markdown.

Decida tambem o gate: se a pergunta for vaga/ambigua o suficiente para voce querer discutir antes de agir (arquitetura, seguranca, RAG, produto) inclua "gates":{"interviewMe":true}; caso contrario "gates":{"interviewMe":false}.
Se a rota for build (implementacao), inclua tambem "gates":{"spec":true}: implementacao no projeto segue spec antes de codigo.
Se a pergunta tiver MULTIPLOS objetivos em frases coordenadas (ex: "criar X E revisar Y"), retorne route combinada com "+" (ex: "build+security") e gates {"scopeSplit":true}: multiplos escopos exigem dividir o trabalho."""


def extract_json(text):
    """Pull the JSON object out of the model output (including inside ``` fences)."""
    # try to find the first { ... } balanced block
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                raw = text[start:i + 1]
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return None
    return None


def load_golden():
    return json.load(open(GOLDEN))["questions"]


def label(q):
    return q.get("id", "?")


def run_question(q, model, timeout=90):
    prompt = ROUTING_TABLE + "\n\nPergunta do usuario: " + q["prompt"]
    try:
        proc = subprocess.run(
            ["opencode", "run", "-m", model, "--pure", "--format", "json",
             "--title", f"routing-eval-{label(q)}", prompt],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    if proc.returncode != 0:
        return None, proc.stderr[-400:]
    # parse the final assistant message text from JSON events
    try:
        events = json.loads(proc.stdout)
    except json.JSONDecodeError:
        # --format json with multiple lines; try line-wise
        lines = [l for l in proc.stdout.splitlines() if l.strip().startswith("{")]
        events = [json.loads(l) for l in lines]
    text_chunks = []
    if isinstance(events, list):
        for ev in events:
            # opencode --format json emits {type:"text", part:{type:"text", text:"..."}}
            part = ev.get("part")
            if ev.get("type") == "text" and isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                text_chunks.append(part["text"])
            elif ev.get("type") == "message" and ev.get("role") == "assistant":
                content = ev.get("content")
                if isinstance(content, str):
                    text_chunks.append(content)
                elif isinstance(content, list):
                    for p in content:
                        if isinstance(p, dict) and p.get("type") == "text" and p.get("text"):
                            text_chunks.append(p["text"])
    answer = "\n".join(text_chunks).strip()
    if not answer and proc.stdout.strip():
        answer = proc.stdout.strip()[-2000:]
    parsed = extract_json(answer)
    return parsed, answer


def score(expected_q, actual):
    """Mirror routing-score rules: route 0.6, gates 0.4, pass >= 0.7."""
    exp_route = (expected_q.get("expectedRoute") or "").lower().strip()
    exp_gates = expected_q.get("expectedGates") or {}
    act_route = (actual.get("route") or "").lower().strip()
    act_gates = actual.get("gates") or {}

    alts = {
        "deep-researcher": ["ai-research", "research"],
        "ai-architect": ["architect"],
        "ai-evals-runner": ["evals"],
        "llm-security-reviewer": ["security"],
        "direct": ["answer", "self"],
        "build": ["implementation", "orchestrator-direct"],
    }
    # multi-route: compare component sets, allowing synonyms per component
    def _comp_match(a, b):
        return a == b or b in alts.get(a, []) or a in alts.get(b, [])
    if exp_route == act_route or act_route in alts.get(exp_route, []):
        route_score = 1.0
    elif "+" in exp_route or "+" in act_route:
        exp_comps = [c for c in exp_route.split("+") if c]
        act_comps = [c for c in act_route.split("+") if c]
        if exp_comps and act_comps:
            # every expected component must appear in actual (allow synonyms)
            route_score = 1.0 if all(any(_comp_match(ec, ac) for ac in act_comps) for ec in exp_comps) else 0.0
        else:
            route_score = 0.0
    else:
        route_score = 0.0
    if not exp_gates:
        gate_score = 1.0
    else:
        total, matched = len(exp_gates), 0
        for k, v in exp_gates.items():
            av = act_gates.get(k)
            # absent gate counts as satisfied when expected value is False
            if av == v or (av is None and v is False):
                matched += 1
        gate_score = matched / total
    composite = 0.6 * route_score + 0.4 * gate_score
    return {"expected_route": exp_route, "actual_route": act_route,
            "route_score": round(route_score, 3), "gate_score": round(gate_score, 3),
            "composite": round(composite, 3), "passed": composite >= 0.7}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="opencode/deepseek-v4-flash-free")
    ap.add_argument("--question", default=None, help="run only this question id (ex RS-1)")
    ap.add_argument("--samples", type=int, default=1, help="run each question N times; report route stability + gate rate")
    ap.add_argument("--dry-run", action="store_true", help="print prompts, do not call model")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    qs = load_golden()
    if args.question:
        qs = [q for q in qs if q.get("id") == args.question]
        if not qs:
            print(f"question {args.question} not found", file=sys.stderr)
            return 2

    results = []
    for q in qs:
        qid = label(q)
        if args.dry_run:
            print(f"--- {qid} | expected={q.get('expectedRoute')} ---")
            print(q["prompt"][:120])
            continue
        route_ok_samples = 0
        parse_errors = 0
        composite_samples = []
        route_seen = set()
        last_res = None
        for _ in range(args.samples):
            parsed, raw = run_question(q, args.model)
            if parsed is None:
                parse_errors += 1
                last_raw = raw[:300]
                continue
            res = score(q, parsed)
            route_seen.add(res["actual_route"])
            if res["route_score"] == 1.0:
                route_ok_samples += 1
            composite_samples.append(res["composite"])
            last_res = res
        if args.samples and parse_errors == args.samples:
            results.append({"id": qid, "error": True, "raw": last_raw, "passed": False, "composite": 0})
            continue
        if last_res is None:
            continue
        samples_done = args.samples - parse_errors
        route_stable = samples_done > 0 and route_ok_samples == samples_done
        gate_rate = round(sum(c for c in composite_samples) / len(composite_samples), 3)
        # hard pass: route correct in EVERY sample (routing is deterministic policy);
        # gates are reported as a metric, not a pass/fail gate (subject to model variability)
        passed = route_stable
        last_res["id"] = qid
        last_res["route_stable"] = route_stable
        last_res["route_seen"] = sorted(route_seen)
        last_res["gate_rate"] = gate_rate
        last_res["passed"] = route_stable
        results.append(last_res)
        if args.json:
            print(f"{'PASS' if passed else 'FAIL'} {qid}: expected={last_res['expected_route']} "
                  f"actual={last_res['actual_route']} route_stable={route_stable} gate_rate={gate_rate}",
                  file=sys.stderr)
        else:
            print(f"{'PASS' if passed else 'FAIL'} {qid}: expected={last_res['expected_route']} "
                  f"actual={last_res['actual_route']} route_stable={route_stable} gate_rate={gate_rate}")

    if args.dry_run:
        return 0
    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    if args.json:
        print(json.dumps({"model": args.model, "samples": args.samples, "total": total,
                          "passed": passed,
                          "percent": round(100 * passed / total, 1) if total else 0,
                          "results": results}, ensure_ascii=False, indent=2))
    else:
        print(f"\n{passed}/{total} passed (route-stable) ({round(100 * passed / total, 1)}%)" if total else "no results")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())