"""
Retrieval-only benchmark with chunk-level labels and an ablation study.

    python -m evaluation.retrieval_eval
    python -m evaluation.retrieval_eval --dataset evaluation/golden_dataset_v2.json

No LLM calls, so no API cost and no rate limits - it takes about a minute
(mostly the cross-encoder). Needs Qdrant + Elasticsearch running with the
knowledge base ingested, same as run_eval.

What it reports
---------------
For every pipeline variant below, over all answerable questions:
  hit@1/3/5, recall@5, MRR, nDCG@5   (see retrieval_metrics.py)
  doc_hit@5   the OLD metric (right PDF somewhere in top 5), for contrast

Variants (the ablation):
  bm25            Elasticsearch BM25 only
  vector          Qdrant (all-MiniLM-L6-v2) only
  hybrid_rrf      BM25 + vector fused with Reciprocal Rank Fusion, no reranker
  hybrid_rerank   the production pipeline: BM25 + vector -> cross-encoder
  hybrid_rerank_no_typo_fix   production minus query_normalizer

Plus, for production:
  candidate_recall   was a relevant chunk in the reranker's input pool at
                     all? (separates "retrievers missed it" from "reranker
                     ranked it too low")
  confidence AUROC   how well the confidence score separates answerable
                     from out-of-scope questions
  breakdown by difficulty, and the worst failures with what was retrieved.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean

from evaluation.retrieval_metrics import (
    auroc,
    evidence_groups,
    groups_matched,
    reciprocal_rank_fusion,
    score_ranking,
)

DEFAULT_DATASET = Path(__file__).parent / "golden_dataset_v2.json"
RESULTS_DIR = Path(__file__).parent.parent / "results"

CANDIDATES = 20   # per retriever, same as RetrievalService
DEPTH = 10        # how deep we score each ranking

PRODUCTION = "hybrid_rerank"
CONFIGS = ["bm25", "vector", "hybrid_rrf", "hybrid_rerank", "hybrid_rerank_no_typo_fix"]
HEADLINE = ["hit@1", "hit@3", "hit@5", "recall@5", "mrr", "ndcg@5", "doc_hit@5"]


def load_dataset(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Pipelines:
    """Runs each retrieval variant, reusing shared work per question."""

    def __init__(self):
        # Imported here so `--help` works without the services running.
        from app.retrieval.keyword_retriever import keyword_retriever
        from app.retrieval.merge import merge_results
        from app.retrieval.reranker import reranker
        from app.retrieval.vector_retriever import vector_retriever
        from app.services.retrieval_service import query_normalizer

        self.kw = keyword_retriever
        self.vec = vector_retriever
        self.merge = merge_results
        self.reranker = reranker
        self.normalizer = query_normalizer

    def _base(self, query: str) -> tuple[list[dict], list[dict]]:
        return (
            self.kw.retrieve(query=query, top_k=CANDIDATES),
            self.vec.retrieve(query=query, top_k=CANDIDATES),
        )

    def run(self, question: str, configs: list[str]) -> dict:
        normalized = self.normalizer.normalize(question)
        bm25, vector = self._base(normalized)
        out: dict[str, dict] = {}

        if "bm25" in configs:
            out["bm25"] = {"ranked": bm25[:DEPTH]}
        if "vector" in configs:
            out["vector"] = {"ranked": vector[:DEPTH]}
        if "hybrid_rrf" in configs:
            out["hybrid_rrf"] = {"ranked": reciprocal_rank_fusion(vector, bm25)[:DEPTH]}

        if "hybrid_rerank" in configs:
            pool = self.merge.merge(vector, bm25)
            out["hybrid_rerank"] = {
                "ranked": self.reranker.rerank(query=normalized, documents=pool, top_k=DEPTH),
                "pool": pool,
            }

        if "hybrid_rerank_no_typo_fix" in configs:
            if normalized == question and "hybrid_rerank" in out:
                out["hybrid_rerank_no_typo_fix"] = out["hybrid_rerank"]
            else:
                raw_bm25, raw_vector = self._base(question)
                pool = self.merge.merge(raw_vector, raw_bm25)
                out["hybrid_rerank_no_typo_fix"] = {
                    "ranked": self.reranker.rerank(query=question, documents=pool, top_k=DEPTH),
                    "pool": pool,
                }

        out["_normalized_query"] = normalized
        return out


def evaluate(dataset: list[dict], configs: list[str]) -> dict:
    from app.services.confidence_service import confidence_service

    pipes = Pipelines()
    per_question = []
    started = time.perf_counter()

    for n, item in enumerate(dataset, start=1):
        runs = pipes.run(item["question"], configs)
        groups = evidence_groups(item.get("evidence"))
        row = {
            "id": item["id"],
            "question": item["question"],
            "difficulty": item.get("difficulty", "easy"),
            "category": item.get("category"),
            "answerable": bool(groups),
            "expected_source": item.get("expected_source"),
            "normalized_query": runs["_normalized_query"],
            "configs": {},
        }

        for name in configs:
            ranked = runs[name]["ranked"]
            texts = [d["text"] for d in ranked]
            entry = {
                "top_sources": [d.get("document_name") for d in ranked[:5]],
                "top_snippets": [d["text"][:160].replace("\n", " ") for d in ranked[:3]],
                "duplicate_texts_in_top10": len(texts) - len(set(texts)),
            }
            if groups:
                entry.update(score_ranking(texts, item["evidence"]))
                entry["doc_hit@5"] = float(
                    item.get("expected_source") in {d.get("document_name") for d in ranked[:5]}
                )
                if "pool" in runs[name]:
                    covered = set()
                    for d in runs[name]["pool"]:
                        covered |= groups_matched(d["text"], groups)
                    entry["candidate_recall"] = len(covered) / len(groups)
                    entry["pool_size"] = len(runs[name]["pool"])
            if name == PRODUCTION:
                entry["confidence"] = confidence_service.calculate_confidence(ranked[:5])
                entry["would_escalate"] = confidence_service.should_escalate(entry["confidence"])
            row["configs"][name] = entry

        per_question.append(row)
        prod = row["configs"].get(PRODUCTION, {})
        mark = "" if not row["answerable"] else f"rank={prod.get('first_relevant_rank')}"
        print(f"[{n}/{len(dataset)}] {row['difficulty']:<14} {mark:<9} {item['question'][:60]}")

    return {
        "per_question": per_question,
        "summary": summarise(per_question, configs),
        "elapsed_s": round(time.perf_counter() - started, 1),
    }


def summarise(rows: list[dict], configs: list[str]) -> dict:
    answerable = [r for r in rows if r["answerable"]]
    oos = [r for r in rows if not r["answerable"]]
    summary: dict = {
        "n_answerable": len(answerable),
        "n_out_of_scope": len(oos),
        "configs": {},
    }

    for name in configs:
        metrics = [r["configs"][name] for r in answerable]
        summary["configs"][name] = {k: mean(m[k] for m in metrics) for k in HEADLINE} if metrics else {}

    if PRODUCTION in configs and answerable:
        prod = [r["configs"][PRODUCTION] for r in answerable]
        summary["configs"][PRODUCTION]["candidate_recall"] = mean(m["candidate_recall"] for m in prod)

        by_diff = defaultdict(list)
        for r in answerable:
            by_diff[r["difficulty"]].append(r["configs"][PRODUCTION])
        summary["production_by_difficulty"] = {
            d: {"n": len(ms), **{k: mean(m[k] for m in ms) for k in ["hit@1", "hit@5", "mrr"]}}
            for d, ms in sorted(by_diff.items())
        }

        pos = [r["configs"][PRODUCTION]["confidence"] for r in answerable]
        neg = [r["configs"][PRODUCTION]["confidence"] for r in oos]
        summary["confidence"] = {
            "auroc_answerable_vs_oos": auroc(pos, neg),
            "mean_answerable": mean(pos) if pos else None,
            "mean_out_of_scope": mean(neg) if neg else None,
            # At the current CONFIDENCE_THRESHOLD:
            "oos_flagged_rate": mean(r["configs"][PRODUCTION]["would_escalate"] for r in oos) if oos else None,
            "answerable_flagged_rate": mean(r["configs"][PRODUCTION]["would_escalate"] for r in answerable),
        }

        dups = sum(r["configs"][PRODUCTION]["duplicate_texts_in_top10"] for r in rows)
        summary["duplicate_chunks_seen"] = dups

    return summary


def _pct(x) -> str:
    return "n/a" if x is None else f"{x * 100:.1f}%"


def _num(x) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def render_markdown(result: dict, dataset_name: str) -> str:
    s = result["summary"]
    lines = [
        f"# Retrieval Benchmark — {datetime.now():%Y-%m-%d %H:%M}",
        "",
        f"Dataset: `{dataset_name}` — {s['n_answerable']} answerable questions with "
        f"chunk-level evidence labels, {s['n_out_of_scope']} out-of-scope. "
        f"Run time {result['elapsed_s']}s.",
        "",
        "## Ablation (answerable questions)",
        "",
        "| Pipeline | Hit@1 | Hit@3 | Hit@5 | Recall@5 | MRR | nDCG@5 | Doc-hit@5 (old metric) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, m in s["configs"].items():
        if not m:
            continue
        label = f"**{name}** (production)" if name == PRODUCTION else name
        lines.append(
            f"| {label} | {_pct(m['hit@1'])} | {_pct(m['hit@3'])} | {_pct(m['hit@5'])} | "
            f"{_pct(m['recall@5'])} | {_num(m['mrr'])} | {_num(m['ndcg@5'])} | {_pct(m['doc_hit@5'])} |"
        )

    if "production_by_difficulty" in s:
        prod = s["configs"][PRODUCTION]
        lines += [
            "",
            f"Candidate recall (relevant chunk anywhere in the reranker's input pool): "
            f"**{_pct(prod['candidate_recall'])}**",
            "",
            "## Production pipeline by difficulty",
            "",
            "| Difficulty | N | Hit@1 | Hit@5 | MRR |",
            "|---|---|---|---|---|",
        ]
        for d, m in s["production_by_difficulty"].items():
            lines.append(f"| {d} | {m['n']} | {_pct(m['hit@1'])} | {_pct(m['hit@5'])} | {_num(m['mrr'])} |")

        c = s["confidence"]
        lines += [
            "",
            "## Confidence score vs. out-of-scope questions",
            "",
            f"- AUROC (answerable vs out-of-scope): **{_num(c['auroc_answerable_vs_oos'])}**",
            f"- Mean confidence: answerable {_num(c['mean_answerable'])}, out-of-scope {_num(c['mean_out_of_scope'])}",
            f"- At the current threshold: {_pct(c['oos_flagged_rate'])} of out-of-scope questions flagged, "
            f"{_pct(c['answerable_flagged_rate'])} of answerable questions wrongly flagged",
        ]
        if s.get("duplicate_chunks_seen"):
            lines += [
                "",
                f"> ⚠️ {s['duplicate_chunks_seen']} duplicate chunk texts showed up in top-10 lists. "
                "The knowledge base was probably ingested more than once (ingestion uses random "
                "uuid4 ids). Reset Qdrant/Elasticsearch and re-ingest before trusting precision numbers.",
            ]

        failures = [
            r for r in result["per_question"]
            if r["answerable"] and (r["configs"][PRODUCTION]["first_relevant_rank"] or 99) > 1
        ]
        failures.sort(key=lambda r: r["configs"][PRODUCTION]["first_relevant_rank"] or 99, reverse=True)
        lines += ["", f"## Misses — relevant chunk not ranked #1 ({len(failures)})", ""]
        for r in failures:
            p = r["configs"][PRODUCTION]
            rank = p["first_relevant_rank"]
            lines.append(f"### {r['id']} ({r['difficulty']}) — rank {rank if rank else 'not in top 10'}")
            lines.append(f"- Q: {r['question']}")
            if r["normalized_query"] != r["question"]:
                lines.append(f"- Normalized query: {r['normalized_query']}")
            lines.append(f"- In candidate pool: {'yes' if p.get('candidate_recall') else 'no'}")
            for i, snip in enumerate(p["top_snippets"], start=1):
                lines.append(f"  {i}. `{snip}`")
            lines.append("")

    return "\n".join(lines)


def print_summary(result: dict) -> None:
    s = result["summary"]
    print("\n" + "=" * 86)
    print(f"RETRIEVAL BENCHMARK  ({s['n_answerable']} answerable, {s['n_out_of_scope']} out-of-scope)")
    print("=" * 86)
    print(f"{'pipeline':<28}" + "".join(f"{k:>9}" for k in HEADLINE))
    for name, m in s["configs"].items():
        if m:
            print(f"{name:<28}" + "".join(f"{m[k]:>9.3f}" for k in HEADLINE))
    if "confidence" in s:
        prod = s["configs"][PRODUCTION]
        print(f"\nproduction candidate recall: {prod['candidate_recall']:.3f}")
        print(f"confidence AUROC (answerable vs OOS): {_num(s['confidence']['auroc_answerable_vs_oos'])}")
        print("\nproduction by difficulty:")
        for d, m in s["production_by_difficulty"].items():
            print(f"  {d:<16} n={m['n']:<3} hit@1={m['hit@1']:.2f} hit@5={m['hit@5']:.2f} mrr={m['mrr']:.2f}")
    print("=" * 86)


def parse_args():
    p = argparse.ArgumentParser(description="Chunk-level retrieval benchmark + ablation.")
    p.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    p.add_argument("--configs", nargs="+", default=CONFIGS, choices=CONFIGS)
    return p.parse_args()


def main():
    args = parse_args()
    dataset = load_dataset(args.dataset)
    print(f"Loaded {len(dataset)} questions from {args.dataset.name}\n")

    result = evaluate(dataset, args.configs)
    print_summary(result)

    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RESULTS_DIR / f"retrieval_eval_{ts}.json"
    md_path = RESULTS_DIR / f"retrieval_eval_{ts}.md"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(result, args.dataset.name), encoding="utf-8")
    print(f"\nSaved:\n  {json_path}\n  {md_path}")


if __name__ == "__main__":
    main()
