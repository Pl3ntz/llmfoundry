#!/usr/bin/env python3
"""research-scorer.py: deterministic recall/fabrication scorer for deep-researcher.

Simulates a "synthetic haystack": a known corpus with planted needles (facts)
hidden among noise, plus a candidate research output. Scores how many needles
the output actually found, how many claims it fabricated, and whether
VERIFIED claims carry a source whose content actually matches.

No LLM involved. Pure string/graph logic so the eval suite stays deterministic
and offline (the same requirement as the rest of eval-runner.py).

Usage (import):  from research_scorer import score_haystack
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Needle:
    """A planted fact the research output must find."""
    id: str
    claim: str          # canonical sentence, unique to this needle
    source: str         # fake URL of the primary source
    content: str        # the actual source text that must match verbatim


@dataclass
class HaystackResult:
    found: List[str] = field(default_factory=list)          # needle ids found
    missed: List[str] = field(default_factory=list)         # needle ids not found
    fabricated: List[str] = field(default_factory=list)     # claims with no matching source
    verified_ok: int = 0                                    # VERIFIED claims with matching source
    verified_bad: int = 0                                   # VERIFIED claims WITHOUT matching source

    @property
    def recall(self) -> float:
        total = len(self.found) + len(self.missed)
        return len(self.found) / total if total else 0.0

    @property
    def fabrication_rate(self) -> float:
        total = len(self.found) + len(self.fabricated)
        return len(self.fabricated) / total if total else 0.0


# ---------------------------------------------------------------------------
# Normalization for matching (case/accents/whitespace/punctuation-insensitive)

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")
_ACCENTS = {
    ord("á"): "a", ord("à"): "a", ord("â"): "a", ord("ã"): "a",
    ord("é"): "e", ord("ê"): "e", ord("í"): "i", ord("ó"): "o",
    ord("ô"): "o", ord("õ"): "o", ord("ú"): "u", ord("ç"): "c",
}


def normalize(text: str) -> str:
    text = text.lower()
    text = text.translate(_ACCENTS)
    text = _PUNCT.sub(" ", text)
    return _WS.sub(" ", text).strip()


def _normalized_tokens(text: str) -> List[str]:
    return normalize(text).split()


def _contains_claim(haystack: str, claim: str) -> bool:
    """True if claim tokens appear consecutively inside haystack (ordered, fuzzy)."""
    tokens = _normalized_tokens(claim)
    hay = _normalized_tokens(haystack)
    if not tokens:
        return True
    n = len(tokens)
    for i in range(len(hay) - n + 1):
        if hay[i : i + n] == tokens:
            return True
    return False


# Stopwords and noise tokens ignored for significance overlap.
_SIGNIFICANT_MIN = 3  # tokens shorter than this are noise (prepositions, articles)
_SIGNIFICANT_STOP = {
    "sobre", "entre", "para", "com", "sem", "por", "em", "de", "do", "da", "dos", "das",
    "que", "quem", "como", "uma", "um", "o", "a", "os", "as", "e", "ou", "mas", "porque",
    "quando", "onde", "foi", "era", "sao", "ser", "mais", "menos", "muito", "pouco", "atual",
    "segundo", "segunda", "informou", "disseram", "dizem", "conforme", "the", "of", "and",
    "in", "on", "at", "to", "for", "with", "was", "is", "are", "were", "a", "an", "it",
}


def _significant_tokens(text: str):
    return [
        t for t in _normalized_tokens(text)
        if len(t) >= _SIGNIFICANT_MIN and t not in _SIGNIFICANT_STOP
    ]


def _significant_overlap(haystack: str, claim: str, threshold: float = 0.6) -> bool:
    """True if >= threshold fraction of the claim's significant tokens appear in
    the haystack (order-insensitive). Catches paraphrase/translation drift that
    exact consecutive-token matching misses."""
    claim_tokens = _significant_tokens(claim)
    if not claim_tokens:
        return True
    hay_tokens = set(_significant_tokens(haystack))
    hits = sum(1 for t in claim_tokens if t in hay_tokens)
    return hits / len(claim_tokens) >= threshold


def _claims_equivalent(a: str, b: str) -> bool:
    """Do two claims refer to the same fact? Exact-ish or significant-overlap."""
    a_norm, b_norm = normalize(a), normalize(b)
    if a_norm == b_norm:
        return True
    if not a_norm or not b_norm:
        return False
    return _contains_claim(a, b) or _contains_claim(b, a) or _significant_overlap(a, b)


# ---------------------------------------------------------------------------
# Core scoring

def score_haystack(
    needles: List[Needle],
    claims: List[str],               # claims the agent reported (plain text lines)
    verified_claims: List[str],      # claims the agent marked VERIFIED
    source_contents: Dict[str, str], # url -> content that the agent's sources claim to contain
    ignore_urls: bool = True,
) -> HaystackResult:
    """Score a candidate output against the synthetic haystack.

    - found: needle whose canonical claim appears (fuzzy) in the agent's claims.
    - missed: needle not found.
    - fabricated: agent claim that does not match ANY needle's canonical claim
      (i.e., an unsupported claim. A needle could be "planted" that is not in
      the corpus, representing confabulation).
    - verified_bad: claim marked VERIFIED whose source content does NOT contain
      the claim text (fabrication hidden behind a VERIFIED label).
    """
    res = HaystackResult()
    claimed_norm = set(normalize(c) for c in claims)

    # 1. recall: which planted needles did the output find?
    for needle in needles:
        if any(_claims_equivalent(c, needle.claim) for c in claims):
            res.found.append(needle.id)
        else:
            res.missed.append(needle.id)

    # 2. fabrication: any agent claim that matches NO needle is fabricated
    for c in claims:
        cn = normalize(c)
        if cn and not any(_claims_equivalent(c, n.claim) for n in needles):
            res.fabricated.append(c)

    # 3. VERIFIED integrity: every VERIFIED claim must have a source whose
    #    content actually contains the claim text.
    for c in verified_claims:
        matched = any(_claims_equivalent(content, c) for content in source_contents.values())
        if matched:
            res.verified_ok += 1
        else:
            res.verified_bad += 1

    return res


if __name__ == "__main__":
    import sys

    print("research-scorer.py: importable module; scoring happens inside eval-runner.py", file=sys.stderr)
    sys.exit(0)
