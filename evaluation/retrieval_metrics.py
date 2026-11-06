"""
Chunk-level retrieval metrics. Pure Python, no services needed.

Why the old "retrieval hit rate" was always 100%
------------------------------------------------
It checked whether the expected *PDF* appeared anywhere in the top 5
chunks. With only 8 PDFs in the knowledge base, 5 chunks almost always
include the right file - even when the chunk that actually holds the answer
was never retrieved. It measured "did we land in the right document", not
"did we find the answer".

What we measure instead
-----------------------
Each golden question carries `evidence`: short verbatim snippets from the
PDF that contain the answer. A retrieved chunk is *relevant* only if it
contains one of those snippets (after normalising case, punctuation and
whitespace, so "5–7 Business Days" matches "5-7 business days"). The
knowledge base has ~96 chunks, so ranking the right one first is a real
test.

`evidence` is a list of groups. A group is one required fact, given as a
string or a list of alternative strings (the same fact may appear in two
places). Multi-hop questions have several groups.

Metrics (standard IR definitions, k = cut-off):
  hit@k        1 if any relevant chunk is in the top k
  recall@k     share of evidence groups covered by the top k
               (= hit@k for single-fact questions)
  mrr          1 / rank of the first relevant chunk (0 if none in list)
  ndcg@k       rank-discounted gain, binary relevance
  precision@k  share of the top k chunks that are relevant
"""

from __future__ import annotations

import math
import re
from statistics import mean

_DASHES = re.compile(r"[‐-―−]")
_NON_WORD = re.compile(r"[^a-z0-9]+")


def normalize(text: str) -> str:
    text = _DASHES.sub("-", (text or "").lower())
    return _NON_WORD.sub(" ", text).strip()


def evidence_groups(evidence) -> list[list[str]]:
    """Accept ["a", ["b", "c"]] and return [["a"], ["b", "c"]], normalised."""
    groups = []
    for group in evidence or []:
        alternatives = [group] if isinstance(group, str) else list(group)
        groups.append([normalize(a) for a in alternatives if normalize(a)])
    return [g for g in groups if g]


def groups_matched(chunk_text: str, groups: list[list[str]]) -> set[int]:
    """Indices of evidence groups this chunk contains."""
    norm = normalize(chunk_text)
    return {
        i for i, alternatives in enumerate(groups)
        if any(a in norm for a in alternatives)
    }


def relevance_vector(chunks: list[str], groups: list[list[str]]) -> list[bool]:
    return [bool(groups_matched(c, groups)) for c in chunks]


def hit_at_k(rel: list[bool], k: int) -> float:
    return 1.0 if any(rel[:k]) else 0.0


def recall_at_k(chunks: list[str], groups: list[list[str]], k: int) -> float:
    if not groups:
        return 0.0
    covered = set()
    for c in chunks[:k]:
        covered |= groups_matched(c, groups)
    return len(covered) / len(groups)


def reciprocal_rank(rel: list[bool]) -> float:
    for i, r in enumerate(rel, start=1):
        if r:
            return 1.0 / i
    return 0.0


def ndcg_at_k(rel: list[bool], k: int, n_relevant_total: int | None = None) -> float:
    dcg = sum(1.0 / math.log2(i + 2) for i, r in enumerate(rel[:k]) if r)
    # The ideal ranking can't contain fewer relevant chunks than we actually
    # observed: if a fact lives in two chunks and both are retrieved, the
    # ideal is two relevant chunks up top, not one. Without this, DCG can
    # exceed IDCG and nDCG goes above 1.
    n_ideal = max(n_relevant_total or 0, sum(rel))
    n_ideal = min(n_ideal, k)
    if n_ideal == 0:
        return 0.0
    idcg = sum(1.0 / math.log2(i + 2) for i in range(n_ideal))
    return dcg / idcg


def precision_at_k(rel: list[bool], k: int) -> float:
    top = rel[:k]
    return sum(top) / k if k else 0.0


def score_ranking(chunks: list[str], evidence, ks=(1, 3, 5, 10)) -> dict:
    """All metrics for one question and one ranked list of chunk texts."""
    groups = evidence_groups(evidence)
    rel = relevance_vector(chunks, groups)
    # Ideal ranking puts at least one relevant chunk per evidence group up
    # top, so a perfect multi-hop answer needs len(groups) relevant chunks.
    n_ideal = max(len(groups), 1)

    out = {"mrr": reciprocal_rank(rel), "first_relevant_rank": None}
    for i, r in enumerate(rel, start=1):
        if r:
            out["first_relevant_rank"] = i
            break
    for k in ks:
        out[f"hit@{k}"] = hit_at_k(rel, k)
        out[f"recall@{k}"] = recall_at_k(chunks, groups, k)
        out[f"ndcg@{k}"] = ndcg_at_k(rel, k, n_ideal)
        out[f"precision@{k}"] = precision_at_k(rel, k)
    return out


def average(rows: list[dict], keys: list[str]) -> dict:
    return {k: (mean(r[k] for r in rows) if rows else None) for k in keys}


def auroc(positive_scores: list[float], negative_scores: list[float]) -> float | None:
    """
    Probability that a random answerable question gets a higher confidence
    than a random out-of-scope one (ties count half). 1.0 = confidence
    perfectly separates them, 0.5 = coin flip.
    """
    if not positive_scores or not negative_scores:
        return None
    wins = 0.0
    for p in positive_scores:
        for n in negative_scores:
            wins += 1.0 if p > n else 0.5 if p == n else 0.0
    return wins / (len(positive_scores) * len(negative_scores))


def reciprocal_rank_fusion(*ranked_lists: list[dict], k: int = 60) -> list[dict]:
    """
    Standard RRF (Cormack et al., 2009): score = sum 1 / (k + rank). Used as
    the "hybrid without reranker" baseline so we can see how much the
    cross-encoder itself adds.
    """
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}
    for ranked in ranked_lists:
        for rank, doc in enumerate(ranked, start=1):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            docs.setdefault(doc_id, doc)
    order = sorted(scores, key=lambda d: scores[d], reverse=True)
    return [docs[d] for d in order]
