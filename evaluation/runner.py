import asyncio
import time

from app.services.confidence_service import confidence_service
from app.services.llm_service import (
    FALLBACK_RESPONSE,
    RATE_LIMITED_RESPONSE,
    llm_service,
)
from app.services.retrieval_service import retrieval_service

from evaluation.llm_judge import judge_answer
from evaluation.metrics import contains_answer, declined_to_answer, retrieval_hit
from evaluation.retrieval_metrics import score_ranking

DEFAULT_DELAY_BETWEEN_ITEMS_S = 1.0
DEFAULT_MAX_RETRIES = 4
DEFAULT_RETRY_BACKOFF_BASE_S = 15.0


def _chunk_level(documents: list[dict], evidence) -> dict:
    if not evidence:
        return {"chunk_hit": None, "chunk_rank": None, "chunk_rr": None}
    scores = score_ranking([d["text"] for d in documents], evidence, ks=(5,))
    return {
        "chunk_hit": bool(scores["hit@5"]),
        "chunk_rank": scores["first_relevant_rank"],
        "chunk_rr": scores["mrr"],
    }


class EvalRunner:
    def __init__(
        self,
        dataset: list[dict],
        delay_between_items_s: float = DEFAULT_DELAY_BETWEEN_ITEMS_S,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_base_s: float = DEFAULT_RETRY_BACKOFF_BASE_S,
    ):
        self.dataset = dataset
        self.delay_between_items_s = delay_between_items_s
        self.max_retries = max_retries
        self.retry_backoff_base_s = retry_backoff_base_s

    async def _generate_with_retry(
        self, context: str, history: str, question: str
    ) -> str:
        answer = FALLBACK_RESPONSE

        for attempt in range(self.max_retries + 1):
            answer = await llm_service.generate_response(
                context=context, history=history, question=question
            )

            if answer not in (FALLBACK_RESPONSE, RATE_LIMITED_RESPONSE):
                return answer

            if attempt < self.max_retries:
                backoff_s = self.retry_backoff_base_s * (2**attempt)
                print(
                    f"    [retry] generation call failed (likely rate "
                    f"limited) — retrying in {backoff_s:.0f}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(backoff_s)

        return answer

    async def _judge_with_retry(
        self, question: str, reference_notes: str, generated_answer: str
    ) -> dict:
        judge_result = {"score": None, "reasoning": "not attempted"}

        for attempt in range(self.max_retries + 1):
            judge_result = await judge_answer(
                question=question,
                reference_notes=reference_notes,
                generated_answer=generated_answer,
            )

            if judge_result["score"] is not None:
                return judge_result

            if attempt < self.max_retries:
                backoff_s = self.retry_backoff_base_s * (2**attempt)
                print(
                    f"    [retry] judge call failed "
                    f"({judge_result['reasoning']}) — retrying in "
                    f"{backoff_s:.0f}s (attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(backoff_s)

        return judge_result

    async def evaluate_item(self, item: dict) -> dict:
        t0 = time.perf_counter()
        retrieval_result = retrieval_service.retrieve(item["question"])
        retrieval_time_s = time.perf_counter() - t0
        documents = retrieval_result["documents"]
        context = retrieval_result["context"]
        confidence = confidence_service.calculate_confidence(documents)
        would_escalate = confidence_service.should_escalate(confidence)
        t1 = time.perf_counter()
        answer = await self._generate_with_retry(
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
            "difficulty": item.get("difficulty", "easy"),
            "expected_source": item.get("expected_source"),
            "generated_answer": answer,
            "confidence": confidence,
            "would_escalate": would_escalate,
            "retrieved_sources": [d.get("document_name") for d in documents],
            "retrieval_hit": retrieval_hit(documents, item.get("expected_source")),
            **_chunk_level(documents, item.get("evidence")),
            "retrieval_time_s": round(retrieval_time_s, 3),
            "generation_time_s": round(generation_time_s, 3),
        }

        if item["question_type"] == "factual":
            result["is_correct"] = contains_answer(answer, item["expected_answer"])
            result["judge_score"] = None
            result["judge_reasoning"] = None
        elif item["question_type"] == "out_of_scope":
            result["is_correct"] = would_escalate or declined_to_answer(answer)
            result["judge_score"] = None
            result["judge_reasoning"] = None
        else:
            judge_result = await self._judge_with_retry(
                question=item["question"],
                reference_notes=item.get("reference_notes", ""),
                generated_answer=answer,
            )
            result["judge_score"] = judge_result["score"]
            result["judge_reasoning"] = judge_result["reasoning"]
            result["is_correct"] = (
                judge_result["score"] is not None and judge_result["score"] >= 3
            )

        return result

    async def run_all(self, on_item_done=None) -> list[dict]:
        results = []
        self.skipped = []
        total = len(self.dataset)

        for index, item in enumerate(self.dataset, start=1):
            try:
                result = await self.evaluate_item(item)
            except Exception as e:
                print(f"  [skip] {item['id']}: {e!r}")
                self.skipped.append({"id": item["id"], "error": repr(e)})
                continue

            results.append(result)

            if on_item_done:
                on_item_done(index, total, result)

            if index < total and self.delay_between_items_s:
                await asyncio.sleep(self.delay_between_items_s)

        return results
