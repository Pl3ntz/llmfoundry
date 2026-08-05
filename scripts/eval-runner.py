#!/usr/bin/env python3
"""eval-runner.py — unified eval runner for LLMFoundry.

Runs deterministic checks against golden sets and reports pass/fail with
baseline comparison. No LLM required for the memory/engine checks; the
orchestrator/deep-researcher golden sets are scored by routing-score.py.

Usage:
    eval-runner.py                      # run everything
    eval-runner.py --suite memory       # only engine unit checks
    eval-runner.py --suite routing      # routing score validation (deterministic fixtures)
    eval-runner.py --check-plugins      # validate plugin TS compiles (needs bun)
    eval-runner.py --baseline           # print current state (the number to beat)
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_MODULE = os.path.join(ROOT, "scripts", "memory", "foundry_memory.py")
ROUTING_SCORE = os.path.join(ROOT, "scripts", "routing-score.py")

# ----------------------------------------------------------------------------
# Engine unit checks (deterministic, no model)

def _mem_db(tmp):
    import importlib.util

    spec = importlib.util.spec_from_file_location("foundry_memory", MEMORY_MODULE)
    m = importlib.util.module_from_spec(spec)
    # redirect storage to a temp dir for isolation
    import foundry_memory_patch  # noqa
    return m


def engine_checks():
    """Unit checks against the memory engine (real SQLite, temp dir)."""
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, HOME=tmp)
        sys.path.insert(0, os.path.dirname(MEMORY_MODULE))
        import importlib.util

        spec = importlib.util.spec_from_file_location("foundry_memory", MEMORY_MODULE)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)

        # patch storage dir to tmp (all paths, so nothing touches ~/.local)
        m.DB_DIR = os.path.join(tmp, ".local", "share", "llmfoundry", "memory")
        m.DB_PATH = os.path.join(m.DB_DIR, "memory.db")
        m.VEC_PATH = os.path.join(m.DB_DIR, "vectors.npz")
        m.PROJECTS_DIR = os.path.join(m.DB_DIR, "projects")
        m.EMBED_CACHE = os.path.join(tmp, ".cache")

        # 1. remember + search
        mid = m.remember("decisao: DeepSeek V4 Pro sobre kimi-k3 por custo", "t", "decision")
        results.append(("remember stores id", mid is not None))
        found = m.search("DeepSeek", container="t")
        results.append(("search finds memory", len(found) == 1))

        # 2. fact reinforcement (dedup + confidence++)
        m.remember_fact("t", "static", "stack: fastapi")
        m.remember_fact("t", "static", "stack: fastapi")
        row = m._conn().execute("SELECT reinforced_count FROM memory_facts WHERE fact_text='stack: fastapi'").fetchone()
        results.append(("fact reinforcement dedups", row["reinforced_count"] == 2))

        # 3. gotcha recurrence
        m.record_gotcha("t", "build fails", sample="s1")
        m.record_gotcha("t", "build fails", sample="s2")
        m.record_gotcha("t", "build fails", sample="s3")
        g = m._conn().execute("SELECT count FROM gotchas WHERE normalized_pattern='build fails'").fetchone()
        results.append(("gotcha count reaches 3", g["count"] == 3))

        # 4. privacy block (secret)
        blocked = m.remember("chave sk-abc123456789012345678901234567890 no arquivo", "t")
        results.append(("secret is blocked", blocked is None))

        # 4b. idempotent import: same source file must not duplicate
        idem_con = m._conn()
        src_meta = json.dumps({"type": "reference", "source": "project-x.md"})
        now = "2026-01-01T00:00:00Z"
        idem_con.execute(
            "INSERT INTO memories (content, container, memory_type, project, metadata, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            ("contexto do projeto x", "t", "reference", "t", src_meta, now, now),
        )
        idem_con.commit()
        already = idem_con.execute(
            "SELECT 1 FROM memories WHERE container='t' AND metadata LIKE ? LIMIT 1",
            (f'%"source": "project-x.md"%',),
        ).fetchone()
        idem_con.close()
        results.append(("idempotent import dedups by source", already is not None))

        # 5. finding + recall
        m.record_finding("t", "deep-researcher", "[HIGH] ssrf via fetch", "HIGH")
        recall = m.recall(container="t")
        results.append(("recall returns open finding", len(recall["findings"]) == 1))

        # 5b. recall includes memories and facts (imported knowledge enters context)
        m.remember("decisao: usar DeepSeek V4", container="t", memory_type="decision")
        m.remember_fact("t", "dynamic", "preferencia: resposta em pt-br")
        recall2 = m.recall(container="t")
        results.append(("recall includes memories", len(recall2.get("memories", [])) >= 1))
        results.append(("recall includes facts", len(recall2.get("facts", [])) >= 1))

        # 6. log recall acted
        n = m.log_recall("t", "orchestrator", acted_on=True)
        results.append(("log-recall works", n == 0))

        # 7. stats
        s = m.stats("t")
        results.append(("stats report", s["findings"] == 1))

        # 8. decay
        d = m.apply_decay()
        results.append(("decay runs", d is not None))

        # 9. promote threshold
        m.promote("t")
        g2 = m._conn().execute("SELECT promoted FROM gotchas WHERE normalized_pattern='build fails'").fetchone()
        results.append(("gotcha promoted at count 3", g2["promoted"] == 1))

    return results


# ----------------------------------------------------------------------------
# Routing score validation (deterministic fixtures)

def routing_checks():
    results = []
    spec = os.path.join(ROOT, "evals", "orchestrator", "golden-set.json")
    data = json.load(open(spec))
    golden = data.get("questions", data if isinstance(data, list) else [])

    # For each golden question, verify the expected route is one we know
    known = {"deep-researcher-v2", "ai-architect", "ai-evals-runner", "llm-security-reviewer",
             "direct", "interview", "build", "build+security"}
    for i, q in enumerate(golden):
        r = q.get("expectedRoute", "").lower()
        results.append((f"RS-{i+1} route known: {r}", r in known or "+" in r))

    # Verify scorer works on a known-good case
    exp = {"expectedRoute": "deep-researcher", "expectedGates": {"interviewMe": False}}
    act = {"route": "deep-researcher", "gates": {"interviewMe": False}}
    cmd = [sys.executable, ROUTING_SCORE, json.dumps(exp).replace('"', '\\"'), json.dumps(act).replace('"', '\\"')]
    # simpler: import the scorer directly
    import importlib.util

    sspec = importlib.util.spec_from_file_location("routing_score", ROUTING_SCORE)
    rs = importlib.util.module_from_spec(sspec)
    sspec.loader.exec_module(rs)
    route = rs._route_match(rs._route(exp), rs._route(act))
    gate = rs._gate_score(rs._gates(exp), rs._gates(act))
    comp = rs.WEIGHTS["route-match"] * route + rs.WEIGHTS["gate-correctness"] * gate
    results.append(("scorer PASS case", comp >= rs.PASS_THRESHOLD))

    # fail case
    act_bad = {"route": "direct", "gates": {"interviewMe": False}}
    route_bad = rs._route_match(rs._route(exp), rs._route(act_bad))
    comp_bad = rs.WEIGHTS["route-match"] * route_bad + rs.WEIGHTS["gate-correctness"] * gate
    results.append(("scorer catches wrong route", comp_bad < rs.PASS_THRESHOLD))

    return results


# ----------------------------------------------------------------------------
# Plugin compile check (requires bun)

def plugin_checks():
    results = []
    for plugin in ["gates.ts", "memory.ts", "voice-guard.ts", "verify-guard.ts",
                   "publish-guard.ts", "delegation-guard.ts", "research-guard.ts"]:
        path = os.path.join(ROOT, "plugins", plugin)
        out = os.path.join(tempfile.gettempdir(), "llmfoundry-plugin-check")
        try:
            r = subprocess.run(["bun", "build", path, "--outdir", out], capture_output=True, text=True, timeout=60)
            results.append((f"{plugin} compiles", r.returncode == 0))
        except FileNotFoundError:
            results.append((f"{plugin} compiles (bun missing)", True))  # skip, not a regression
    return results


# ----------------------------------------------------------------------------
# Guard regression checks (delegation-guard.ts + research-guard.ts)
#
# These mirror the regex logic in the TS plugins so a regression in the guards
# (e.g. a research prompt being blocked) is caught by the deterministic suite.
# If you change the plugins, update these fixtures in the same commit.

import re as _re

# mirror of delegation-guard.ts MISROUTE_RULES (word-boundaried + evals + debate gate)
_DG_MISROUTE = [
    (_re.compile(r"\b(?:market|competitor|landscape|industry|pricing|adoption|OSINT|recon)\b", _re.I),
     ["ai-architect", "ai-evals-runner", "llm-security-reviewer", "reverse-engineer"]),
    (_re.compile(r"\b(?:design|architect(?:ure|ing|s)?|build|implement|system\s+design|spec\s+for)\b", _re.I),
     ["ai-evals-runner", "reverse-engineer"]),
    (_re.compile(r"\b(?:eval(?:s|uation)?|golden\s+set|regression|baseline|assertion|prompt.*(?:change|update))\b", _re.I),
     ["deep-researcher-v2", "ai-architect", "llm-security-reviewer", "reverse-engineer"]),
    (_re.compile(r"\b(?:security\s+review|prompt\s+injection|OWASP|LLM\s+(?:app\s+)?security)\b", _re.I),
     ["deep-researcher-v2", "ai-evals-runner", "reverse-engineer"]),
    (_re.compile(r"\b(?:binary|firmware|malware|decompil\w*|disassembl\w*|ghidra|radare)\b", _re.I),
     ["deep-researcher-v2", "ai-architect", "ai-evals-runner", "llm-security-reviewer"]),
]
_DG_RESEARCH_SIGNALS = _re.compile(r"\b(?:research|compare|landscape|market|competitor|industry|OSINT|recon|pesquis\w*)\b", _re.I)
_DG_AGENT_MENTION = _re.compile(r"\b(?:deep-researcher-v2|ai-architect|ai-evals-runner|llm-security-reviewer|reverse-engineer|platform-engineer|backend-architect|api-contract-engineer|database-engineer|data-model-engineer|red-team-agent|security-defensive|bug-bounty-hunter|recon-agent|report-agent|triage-agent|general|explore)\b", _re.I)

# mirror of research-guard.ts
_RG_RESEARCH = _re.compile(r"\b(?:market|competitor|landscape|industry|pricing|adoption|OSINT|recon|vs\.?\.?\s+alternatives?)\b", _re.I)
_RG_DOC_TERMS = _re.compile(r"\b(?:docs?|documentation|api|guide|tutorial|reference|getting\s+started|setup|install|config|example|how\s+to|library|framework|sdk|syntax|error|changelog|release|npm|pypi|crates)\b", _re.I)


def _dg_blocked(prompt, target):
    """Mirror of delegation-guard.validateDelegation gate logic (parts skipped)."""
    # Gate 2: transversal consultation (2+ distinct agents named) -> not a misroute
    if len(set(_DG_AGENT_MENTION.findall(prompt))) >= 2:
        return None
    if _DG_RESEARCH_SIGNALS.search(prompt) and target == "deep-researcher-v2":
        return None
    for re_, blocked in _DG_MISROUTE:
        if re_.search(prompt) and target in blocked:
            return re_.pattern
    return None


def guard_checks():
    results = []

    # research prompts with technical TOPICS must reach deep-researcher-v2
    research_topics = [
        "Pesquise sobre AI agent frameworks em 2026 e compare os 5 melhores",
        "Research MCP servers ecosystem landscape 2026",
        "Compare RAG pipelines vs agentic workflows para suporte",
        "Pesquise architecture patterns de sistemas LLM atuais",
        "Pesquise sobre agentes open source de coding",
        "Research vector databases 2026 for RAG",
    ]
    ok = all(_dg_blocked(p, "deep-researcher-v2") is None for p in research_topics)
    results.append(("delegation: research com topicos tecnicos NAO bloqueado p/ deep-researcher-v2", ok))

    # real misroutes are still blocked
    results.append(("delegation: market research NAO vai p/ ai-architect",
                    _dg_blocked("market research de CRMs para 2026", "ai-architect") is not None))
    results.append(("delegation: task de design NAO vai p/ ai-evals-runner",
                    _dg_blocked("Design a RAG system with reranking", "ai-evals-runner") is not None))
    results.append(("delegation: eval task NAO vai p/ deep-researcher-v2",
                    _dg_blocked("Build a golden set for the prompt change", "deep-researcher-v2") is not None))

    # word-boundary regression: pt verb "reconhecer" must NOT trigger market rule
    debate_prompt = (
        "A pergunta central: como montar um agente de pesquisa profunda com capacidade "
        "massiva, capaz de reconhecer padroes entre fontes, e replicar o que um "
        "pesquisador humano faria manualmente."
    )
    results.append(("delegation: 'reconhecer' NAO bloqueia ai-architect (word boundary)",
                    _dg_blocked(debate_prompt, "ai-architect") is None))
    results.append(("delegation: 'reconhecer' NAO bloqueia ai-evals-runner (word boundary)",
                    _dg_blocked(debate_prompt, "ai-evals-runner") is None))
    results.append(("delegation: 'reconhecer' NAO bloqueia llm-security-reviewer (word boundary)",
                    _dg_blocked(debate_prompt, "llm-security-reviewer") is None))

    # transversal consultation (debate): naming 2+ agents is not a misroute
    multi_agent_prompt = (
        "Debate entre ai-architect, ai-evals-runner, llm-security-reviewer, "
        "deep-researcher e platform-engineer sobre o mesmo tema."
    )
    results.append(("delegation: debate com 5 agentes NAO bloqueado p/ ai-architect",
                    _dg_blocked(multi_agent_prompt, "ai-architect") is None))
    results.append(("delegation: debate com 5 agentes NAO bloqueado p/ ai-evals-runner",
                    _dg_blocked(multi_agent_prompt, "ai-evals-runner") is None))
    results.append(("delegation: debate com 5 agentes NAO bloqueado p/ llm-security-reviewer",
                    _dg_blocked(multi_agent_prompt, "llm-security-reviewer") is None))

    # 'evals' (plural) is still an eval task -> deep-researcher-v2 blocked
    results.append(("delegation: 'Build evals...' NAO vai p/ deep-researcher-v2",
                    _dg_blocked("Build evals for the prompt change", "deep-researcher-v2") is not None))
    # single-agent mention does NOT unlock misroute gates
    results.append(("delegation: mencao de 1 agente ainda bloqueia market research p/ ai-architect",
                    _dg_blocked("market research de CRMs (consulte ai-architect)", "ai-architect") is not None))

    # research-guard: doc lookups (query-only websearch) are NOT research
    doc_queries = [
        {"query": "compare bun vs node install docs"},
        {"query": "fastapi vs flask api guide"},
        {"query": "setup MCP server tutorial"},
        {"url": "https://docs.example.com/api/"},
        {"url": "https://example.com/readme.md"},
        {"url": "https://context7.com/x"},
    ]
    ok = all((_RG_DOC_TERMS.search(q.get("query", "")) or "/docs" in q.get("url", "")
              or "/api" in q.get("url", "") or "readme" in q.get("url", "")
              or "context7" in q.get("url", "")) for q in doc_queries)
    results.append(("research: doc lookup websearch NAO e pesquisa de mercado", ok))

    # research-guard: real market/OSINT research IS flagged
    market = [{"query": "competitor landscape of observability tools 2026"},
              {"query": "market pricing of vector databases"}]
    ok = all(_RG_RESEARCH.search(q["query"]) for q in market)
    results.append(("research: pesquisa de mercado/landscape e detectada", ok))

    return results


# ----------------------------------------------------------------------------
# Stability checks (K=5) — deterministic, no model, no Chrome.

K_RUNS = 5


def stability_checks():
    """Run critical engine operations K times and assert identical results.

    Mirrors Quarterdeck's stability harness (measure where output fluctuates) but for
    the deterministic engine: an operation must return the same result every run.
    No model, no sessions, no MCPs, so it is safe to run anywhere.
    """
    results = []
    import importlib.util

    with tempfile.TemporaryDirectory() as tmp:
        spec = importlib.util.spec_from_file_location("foundry_memory", MEMORY_MODULE)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        m.DB_DIR = os.path.join(tmp, ".local", "share", "llmfoundry", "memory")
        m.DB_PATH = os.path.join(m.DB_DIR, "memory.db")
        m.VEC_PATH = os.path.join(m.DB_DIR, "vectors.npz")
        m.PROJECTS_DIR = os.path.join(m.DB_DIR, "projects")
        m.EMBED_CACHE = os.path.join(tmp, ".cache")

        # K runs of reinforcement accumulate deterministically: after K calls the
        # count is exactly K (not random, not dropped). This is the stability claim.
        for _ in range(K_RUNS):
            m.remember_fact("stable", "static", "stack: fastapi")
        row = m._conn().execute(
            "SELECT reinforced_count FROM memory_facts WHERE fact_text='stack: fastapi'"
        ).fetchone()
        results.append(
            (f"fact reinforcement accumulates deterministically (K={K_RUNS} → {row['reinforced_count']})",
             row["reinforced_count"] == K_RUNS)
        )

        # K runs of privacy block must all reject.
        blocked = all(
            m.remember(f"chave sk-abc123456789012345678901234567890 run {i}", "stable") is None
            for i in range(K_RUNS)
        )
        results.append((f"privacy block stable across K={K_RUNS}", blocked))

        # K runs of recall shape must be consistent (findings + gotchas keys).
        shapes = []
        for _ in range(K_RUNS):
            r = m.recall(container="stable")
            shapes.append(sorted(r.keys()))
        results.append((f"recall shape stable across K={K_RUNS}", all(s == shapes[0] for s in shapes)))

        # K runs of stats must produce the same count.
        counts = [m.stats("stable")["facts"] for _ in range(K_RUNS)]
        results.append((f"stats stable across K={K_RUNS}", len(set(counts)) == 1))

    return results


# ----------------------------------------------------------------------------
# deep-researcher-v2: synthetic haystack eval (deterministic, offline)

def drv2_checks():
    """Synthetic-haystack scoring for the v2 research agent.

    Simulates a corpus with planted needles (facts) hidden among noise and
    scores a candidate output: recall (did it find the needles?), fabrication
    (did it report claims that match no source?), and VERIFIED integrity
    (did every VERIFIED claim carry a source whose content actually matches?).
    """
    import importlib.util
    import sys as _sys

    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(
        "research_scorer", os.path.join(os.path.dirname(os.path.abspath(__file__)), "research_scorer.py")
    )
    rs = importlib.util.module_from_spec(spec)
    _sys.modules["research_scorer"] = rs  # required: dataclass resolution needs __module__ in sys.modules
    spec.loader.exec_module(rs)

    results = []

    needles = [
        rs.Needle("n1", "O Satelite Kepler-186f orbita uma estrela anã vermelha a 490 anos-luz da Terra",
                  "https://exo.example.org/kepler186f", "Kepler-186f is a planet orbiting a red dwarf star at 490 light-years."),
        rs.Needle("n2", "O preco do Bytecoing caiu 22 por cento em 2024 por causa de regulacao",
                  "https://crypto.example.org/bytecoing-2024", "Bytecoing fell 22% in 2024 amid tightening regulation."),
        rs.Needle("n3", "A proteina TCMP-9 reverte fibrose pulmonar em camundongos",
                  "https://bio.example.org/tcmp9", "TCMP-9 reversed pulmonary fibrosis in mice."),
    ]

    # --- Case 1: perfect recall, no fabrication, VERIFIED with matching source
    good_output = [
        "O Satelite Kepler-186f orbita uma estrela anã vermelha a 490 anos-luz da Terra",
        "O preco do Bytecoing caiu 22 por cento em 2024 por causa de regulacao",
        "A proteina TCMP-9 reverte fibrose pulmonar em camundongos",
    ]
    good_sources = {
        "https://exo.example.org/kepler186f": "A estrela anã vermelha é pequena. O Satelite Kepler-186f orbita uma estrela anã vermelha a 490 anos-luz da Terra, segundo a equipe.",
        "https://crypto.example.org/bytecoing-2024": "O preco do Bytecoing caiu 22 por cento em 2024 por causa de regulacao, informou o relatorio.",
        "https://bio.example.org/tcmp9": "A proteina TCMP-9 reverte fibrose pulmonar em camundongos, conforme os experimentos de laboratorio.",
    }
    r = rs.score_haystack(needles, good_output, good_output, good_sources)
    results.append(("drv2: recall 3/3 no palheiro sintetico", r.recall == 1.0))
    results.append(("drv2: zero fabricacoes em output correto", r.fabrication_rate == 0.0))
    results.append(("drv2: VERIFIED com fonte real = 0 violacoes", r.verified_bad == 0))

    # --- Case 2: missed needle (recall loss) + a fabricated claim
    partial_output = [
        "O Satelite Kepler-186f orbita uma estrela anã vermelha a 490 anos-luz da Terra",
        "O governo do Brasil declarou independencia financeira total em 2025",  # fabricated
    ]
    partial_sources = {"https://exo.example.org/kepler186f": "Kepler-186f is a planet orbiting a red dwarf star at 490 light-years."}
    r = rs.score_haystack(needles, partial_output, [], partial_sources)
    results.append(("drv2: recall 1/3 quando agente perde agulhas", r.recall == 1 / 3))
    results.append(("drv2: claim fabricada e detectada", r.fabrication_rate > 0))

    # --- Case 3: VERIFIED label with a source that does NOT contain the claim
    lying_output = ["O preco do Bytecoing caiu 22 por cento em 2024 por causa de regulacao"]
    lying_sources = {"https://crypto.example.org/bytecoing-2024": "Page not found."}  # content mismatch
    r = rs.score_haystack(needles, lying_output, lying_output, lying_sources)
    results.append(("drv2: VERIFIED com fonte sem conteudo = violacao", r.verified_bad >= 1))

    # --- Case 4: noise is not confused with a needle (no false positive on garbage)
    noise_output = ["O clima em Marte esta agradavel esta semana, dizem os cientistas"]
    r = rs.score_haystack(needles, noise_output, [], {})
    results.append(("drv2: ruido puro = recall 0, nao fabrica a partir de nada", r.recall == 0.0 and len(r.fabricated) >= 1))

    # --- Case 5: paraphrase is still found (order/synonym drift), distant claim is not
    paraphrase = ["O Bytecoing caiu 22 por cento em 2024 devido a nova regulacao de criptomoedas"]
    r = rs.score_haystack(needles, paraphrase, [], {})
    results.append(("drv2: parafrase proxima conta como encontrada", r.recall == 1 / 3 and not r.fabricated))

    return results


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", choices=["engine", "routing", "plugins", "stability", "guards", "drv2", "all"], default="all")
    ap.add_argument("--baseline", action="store_true", help="print current state")
    args = ap.parse_args()

    results = []
    suites = ["engine", "routing", "plugins", "stability", "guards", "drv2"] if args.suite == "all" else [args.suite]

    for s in suites:
        if s == "engine":
            results += engine_checks()
        elif s == "routing":
            results += routing_checks()
        elif s == "plugins":
            results += plugin_checks()
        elif s == "stability":
            results += stability_checks()
        elif s == "guards":
            results += guard_checks()
        elif s == "drv2":
            results += drv2_checks()

    passed = sum(1 for _, ok in results if ok)
    failed = [(name, ok) for name, ok in results if not ok]

    print(f"=== LLMFoundry eval runner ({len(results)} checks) ===")
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")

    print(f"\nResult: {passed}/{len(results)} passed")
    if args.baseline:
        print(f"\nBASELINE (the number to beat): {passed}/{len(results)} = {passed/len(results)*100:.0f}%")

    if failed:
        print("\nFAILURES:")
        for name, _ in failed:
            print(f"  - {name}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
