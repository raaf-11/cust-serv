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

Rate-limit handling: llm_service.generate_response() swallows API errors
internally and returns FALLBACK_RESPONSE on ANY failure (timeout, 4xx,
5xx, rate limit, etc.) — see app/services/llm_service.py. That means a
string-equality check against FALLBACK_RESPONSE is the only signal this
eval has that a call failed; it can't distinguish "rate limited" from
"genuinely down". Given how eval calls are batched (~1 request per
question, sequentially, plus judge calls), a rate limit is by far the
most likely cause in practice, so a small delay between items plus
exponential-backoff retries are enough to route around it without
touching llm_service.py's error handling itself.
"""

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

# llm_service now throttles itself to LLM_REQUESTS/TOKENS_PER_MINUTE and
# retries 429s (see app/services/llm_rate_limiter.py), so a long fixed
# pause between questions is no longer needed. The retries below are a
# second safety net for anything that still slips through.
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
        """
        Retries generate_response with exponential backoff whenever it
        returns FALLBACK_RESPONSE (our only visible signal of an API
        failure — see module docstring). Gives up and returns the
        fallback string after max_retries.
        """

        answer = FALLBACK_RESPONSE

        for attempt in range(self.max_retries + 1):
            answer = await llm_service.generate_response(
                context=context, history=history, question=question
            )

            if answer not in (FALLBACK_RESPONSE, RATE_LIMITED_RESPONSE):
                return answer

            if attempt < self.max_retries:
                backoff_s = self.retry_backoff_base_s * (2 ** attempt)
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
        """Same retry strategy as _generate_with_retry, for the judge call."""

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
                backoff_s = self.retry_backoff_base_s * (2 ** attempt)
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
            # Chunk-level: did a chunk that actually contains the answer
            # come back, and at what rank? None when the item has no
            # `evidence` labels (e.g. golden_dataset v1).
            **_chunk_level(documents, item.get("evidence")),
            "retrieval_time_s": round(retrieval_time_s, 3),
            "generation_time_s": round(generation_time_s, 3),
        }

        if item["question_type"] == "factual":
            result["is_correct"] = contains_answer(answer, item["expected_answer"])
            result["judge_score"] = None
            result["judge_reasoning"] = None
        elif item["question_type"] == "out_of_scope":
            # The knowledge base can't answer these. Correct behaviour is to
            # not make something up: either the confidence check flags it
            # (the app would ask to rephrase / escalate) or the model says
            # it doesn't have the information.
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
        and avoids hammering the LLM API's rate limits), with a small
        delay between items on top of the per-call retry/backoff in
        _generate_with_retry / _judge_with_retry.

        on_item_done(index, total, result), if given, is called after each
        item so callers (like run_eval.py) can show progress.
        """

        results = []
        self.skipped = []
        total = len(self.dataset)

        for index, item in enumerate(self.dataset, start=1):
            try:
                result = await self.evaluate_item(item)
            except Exception as e:
                # One bad question (e.g. a persistent rate limit) shouldn't
                # throw away the whole run. Skip it and report it at the end.
                print(f"  [skip] {item['id']}: {e!r}")
                self.skipped.append({"id": item["id"], "error": repr(e)})
                continue

            results.append(result)

            if on_item_done:
                on_item_done(index, total, result)

            if index < total and self.delay_between_items_s:
                await asyncio.sleep(self.delay_between_items_s)

        return results
