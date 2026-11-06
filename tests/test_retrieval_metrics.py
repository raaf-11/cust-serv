"""
Unit tests for chunk-level retrieval metrics and the v2 golden dataset.
No services needed:  pytest tests/test_retrieval_metrics.py -q
"""

import json
from pathlib import Path

import pytest

from evaluation.retrieval_metrics import (
    auroc,
    evidence_groups,
    normalize,
    reciprocal_rank_fusion,
    score_ranking,
)

DATASET_V2 = Path(__file__).parent.parent / "evaluation" / "golden_dataset_v2.json"

CHUNKS = [
    "Shipping: Standard Shipping\n5–7 Business Days\nFree on orders ■999+",
    "UPI / Net Banking\nOriginal account\n3–5 business days",
    "Credit / Debit Card\nOriginal card\n5–7 business days",
]


def test_normalize_handles_dashes_case_and_layout():
    assert normalize("5–7 Business\nDays") == normalize("5-7 business days")


def test_right_document_wrong_chunk_is_a_miss():
    # The old doc-level metric would call this a hit: same PDF, wrong row.
    ranked = [CHUNKS[2], CHUNKS[0]]
    s = score_ranking(ranked, ["UPI / Net Banking Original account 3–5 business days"])
    assert s["hit@5"] == 0
    assert s["mrr"] == 0


def test_rank_metrics():
    ranked = [CHUNKS[0], CHUNKS[2], CHUNKS[1]]
    s = score_ranking(ranked, ["UPI / Net Banking"])
    assert s["first_relevant_rank"] == 3
    assert s["hit@1"] == 0 and s["hit@3"] == 1
    assert s["mrr"] == pytest.approx(1 / 3)
    assert 0 < s["ndcg@5"] < 1


def test_multi_hop_recall_needs_every_group():
    ev = ["UPI / Net Banking", "Credit / Debit Card"]
    assert score_ranking([CHUNKS[1]], ev)["recall@5"] == 0.5
    assert score_ranking([CHUNKS[1], CHUNKS[2]], ev)["recall@5"] == 1.0


def test_alternatives_within_a_group():
    groups = evidence_groups([["not here", "Original card"]])
    assert score_ranking([CHUNKS[2]], [["not here", "Original card"]])["hit@1"] == 1
    assert len(groups) == 1


def test_auroc():
    assert auroc([0.9, 0.8], [0.1, 0.2]) == 1.0
    assert auroc([0.5], [0.5]) == 0.5
    assert auroc([], [0.1]) is None


def test_rrf_rewards_agreement():
    a = [{"id": "x"}, {"id": "y"}]
    b = [{"id": "y"}, {"id": "z"}]
    assert [d["id"] for d in reciprocal_rank_fusion(a, b)][0] == "y"


def test_v2_dataset_is_well_formed():
    data = json.loads(DATASET_V2.read_text(encoding="utf-8"))
    ids = [d["id"] for d in data]
    assert len(ids) == len(set(ids))
    for d in data:
        if d["question_type"] == "out_of_scope":
            assert d["evidence"] == []
        else:
            assert evidence_groups(d["evidence"]), d["id"]
            assert d["expected_source"], d["id"]
        if d["question_type"] == "factual":
            assert d.get("expected_answer"), d["id"]
        if d["question_type"] == "open_ended":
            assert d.get("reference_notes"), d["id"]


def test_ndcg_never_exceeds_one_when_fact_repeats_across_chunks():
    # One evidence group, but the fact appears in two retrieved chunks.
    chunks = ["the link is valid for 15 minutes", "reset link valid for 15 minutes", "other"]
    s = score_ranking(chunks, ["valid for 15 minutes"], ks=(5,))
    assert s["ndcg@5"] == 1.0
    s = score_ranking(["other", *chunks], ["valid for 15 minutes"], ks=(5,))
    assert 0 < s["ndcg@5"] < 1
