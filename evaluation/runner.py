"""
Drives the real retrieval + confidence + generation pipeline against the
golden dataset. Reuses the app's own services (not the HTTP API) so it's
fast to run locally and doesn't need a user/session/JWT setup.

Deliberately bypasses ChatService: production ChatService stops and shows
a canned message the moment should_escalate is True, so we'd never learn
whether the *answer itself* would have been right or wrong. Here we always
generate an answer, and separately record whether the confidence score
would have triggered escalation, so calibration can be measured (see
metrics.aggregate_report).

Requires Qdrant, Elasticsearch, and the LLM API key to be reachable, and
the knowledge base already ingested (see evaluation/README.md).
"""

import time

from app.services.confidence_service import confidence_service
from app.services.llm_service import llm_service
from app.services.retrieval_service import retrieval_service

from evaluation.llm_judge import judge_answer
from evaluation.metrics import contains_answer, retrieval_hit


class EvalRunner:

    def __init__(self, dataset: list[dict]):
        self.dataset = dataset

    async def evaluate_item(self, item: dict) -> dict:

        t0 = time.perf_counter()
        retrieval_result = retrieval_service.retrieve(item["question"])
        retrieval_time_s = time.perf_counter() - t0

        documents = retrieval_result["documents"]
        context = retrieval_result["context"]

        confidence = confidence_service.calculate_confidence(documents)
        would_escalate = confidence_service.should_escalate(confidence)

        t1 = time.perf_counter()
        answer = await llm_service.generate_response(
            context=context,
            history="",
            question=item["question"],
        )
        generation_time_s = time.perf_counter() - t1

        result = {
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "question_type": item["question_type"],
            "expected_source": item.get("expected_source"),
            "generated_answer": answer,
            "confidence": confidence,
            "would_escalate": would_escalate,
            "retrieved_sources": [d.get("document_name") for d in documents],
            "retrieval_hit": retrieval_hit(documents, item.get("expected_source")),
            "retrieval_time_s": round(retrieval_time_s, 3),
            "generation_time_s": round(generation_time_s, 3),
        }

        if item["question_type"] == "factual":
            result["is_correct"] = contains_answer(answer, item["expected_answer"])
            result["judge_score"] = None
            result["judge_reasoning"] = None
        else:
            judge_result = await judge_answer(
                question=item["question"],
                reference_notes=item.get("reference_notes", ""),
                generated_answer=answer,
            )
            result["judge_score"] = judge_result["score"]
            result["judge_reasoning"] = judge_result["reasoning"]
            # score >= 3 ("partially correct" or better) counts as correct
            # for pass/fail and calibration purposes.
            result["is_correct"] = (
                judge_result["score"] is not None and judge_result["score"] >= 3
            )

        return result

    async def run_all(self, on_item_done=None) -> list[dict]:
        """
        Runs every item sequentially (deliberately not parallel — keeps
        load on the local Qdrant/Elasticsearch/cross-encoder reasonable
        and avoids hammering the LLM API's rate limits).

        on_item_done(index, total, result), if given, is called after each
        item so callers (like run_eval.py) can show progress.
        """

        results = []
        total = len(self.dataset)

        for index, item in enumerate(self.dataset, start=1):
            result = await self.evaluate_item(item)
            results.append(result)

            if on_item_done:
                on_item_done(index, total, result)

        return results
