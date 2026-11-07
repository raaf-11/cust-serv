import asyncio
import json
from pathlib import Path

import pytest

from evaluation.metrics import aggregate_report
from evaluation.runner import EvalRunner

DATASET_PATH = Path(__file__).parent.parent / "evaluation" / "golden_dataset.json"

MIN_RETRIEVAL_HIT_RATE = 0.80
MIN_FACTUAL_ACCURACY = 0.75
MIN_AVG_JUDGE_SCORE = 3.0
MAX_MISSED_ESCALATION_RATE = 0.25


@pytest.fixture(scope="session")
def eval_report(require_live_services):
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    runner = EvalRunner(dataset)
    results = asyncio.run(runner.run_all())
    report = aggregate_report(results)
    return report, results


def test_retrieval_hit_rate(eval_report):
    report, _ = eval_report
    assert report["retrieval_hit_rate"] is not None
    assert report["retrieval_hit_rate"] >= MIN_RETRIEVAL_HIT_RATE, (
        f"Retrieval hit rate {report['retrieval_hit_rate']:.0%} is below the "
        f"{MIN_RETRIEVAL_HIT_RATE:.0%} threshold. Check ingestion completeness "
        f"or retriever/reranker tuning (top_k, chunk size)."
    )


def test_factual_answer_accuracy(eval_report):
    report, _ = eval_report
    assert report["factual_accuracy"] is not None
    assert report["factual_accuracy"] >= MIN_FACTUAL_ACCURACY, (
        f"Factual answer accuracy {report['factual_accuracy']:.0%} is below "
        f"the {MIN_FACTUAL_ACCURACY:.0%} threshold. Check the markdown report's "
        f"'Failures' section for the specific answers that missed."
    )


def test_open_ended_judge_score(eval_report):
    report, _ = eval_report

    if report["avg_judge_score"] is None:
        pytest.skip("No open-ended questions were successfully judged.")

    assert report["avg_judge_score"] >= MIN_AVG_JUDGE_SCORE, (
        f"Average LLM-judge score {report['avg_judge_score']:.2f}/5 is below "
        f"the {MIN_AVG_JUDGE_SCORE:.2f} threshold."
    )


def test_confidence_calibration(eval_report):
    report, _ = eval_report

    assert report["missed_escalation_rate"] <= MAX_MISSED_ESCALATION_RATE, (
        f"{report['missed_escalation_rate']:.0%} of wrong answers were shown "
        f"to the customer without being escalated to a human — the confidence "
        f"threshold (app/services/confidence_service.py) may be too lax."
    )
