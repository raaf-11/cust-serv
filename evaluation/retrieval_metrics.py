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
    groups = []
    for group in evidence or []:
        alternatives = [group] if isinstance(group, str) else list(group)
        groups.append([normalize(a) for a in alternatives if normalize(a)])
    return [g for g in groups if g]


def groups_matched(chunk_text: str, groups: list[list[str]]) -> set[int]:
    norm = normalize(chunk_text)
    return {
        i
        for i, alternatives in enumerate(groups)
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
    groups = evidence_groups(evidence)
    rel = relevance_vector(chunks, groups)
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
    if not positive_scores or not negative_scores:
        return None
    wins = 0.0
    for p in positive_scores:
        for n in negative_scores:
            wins += 1.0 if p > n else 0.5 if p == n else 0.0
    return wins / (len(positive_scores) * len(negative_scores))


def reciprocal_rank_fusion(*ranked_lists: list[dict], k: int = 60) -> list[dict]:
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}
    for ranked in ranked_lists:
        for rank, doc in enumerate(ranked, start=1):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            docs.setdefault(doc_id, doc)
    order = sorted(scores, key=lambda d: scores[d], reverse=True)
    return [docs[d] for d in order]
