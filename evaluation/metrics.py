"""
Pure, dependency-free scoring functions used by the eval harness.

Kept separate from runner.py so they can be unit tested without needing
Qdrant / Elasticsearch / an LLM API key.
"""

import re
from statistics import mean

STOPWORDS = {
    "a", "an", "the", "is", "are", "of", "to", "for", "and", "or",
    "business", "days", "day", "year", "years", "hours", "hour",
    "minutes", "minute", "weeks", "week", "seconds", "second",
    "attempts", "attempt", "within",
}


NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "fifteen": "15", "eighteen": "18",
    "twenty": "20", "thirty": "30",
}
_NUMBER_WORD_RE = re.compile(r"\b(" + "|".join(NUMBER_WORDS) + r")\b")


def normalize_text(text: str) -> str:
    """Lowercase, unify dash variants, strip punctuation, collapse whitespace,
    and turn number words into digits ("three" -> "3")."""

    text = text.lower()
    text = _NUMBER_WORD_RE.sub(lambda m: NUMBER_WORDS[m.group(1)], text)
    text = text.replace("\u2013", "-").replace("\u2014", "-")  # en/em dash -> hyphen
    text = re.sub(r"[^\w\s\-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _expand_ranges(text: str) -> str:
    """Turn '3-5' into '3 5' so 'X to Y' phrasing still matches on tokens."""

    return re.sub(r"(\d+)-(\d+)", r"\1 \2", text)


def contains_answer(generated: str, expected: str) -> bool:
    """
    Checks whether a generated answer contains the expected fact.

    Tries an exact normalized substring match first (catches the common
    case where the model echoes the phrasing closely), then falls back to
    a token-level check so reasonable paraphrasing (e.g. "3 to 5 business
    days" vs "3-5 business days") still counts.

    This is a heuristic, not a guarantee of correctness — spot-check
    borderline items in the detailed report rather than trusting this
    blindly, especially for numeric ranges.
    """

    if not generated:
        return False

    norm_generated = normalize_text(generated)
    norm_expected = normalize_text(expected)

    if norm_expected in norm_generated:
        return True

    expanded_expected = _expand_ranges(norm_expected)
    tokens = [t for t in expanded_expected.split() if t not in STOPWORDS]

    if not tokens:
        return False

    expanded_generated_tokens = _expand_ranges(norm_generated).split()

    return all(token in expanded_generated_tokens for token in tokens)


NO_INFO_PHRASES = (
    "i don't have enough information",
    "i do not have enough information",
    "i don’t have enough information",
)


def declined_to_answer(generated: str) -> bool:
    """True if the model said it can't answer (the prompt's fallback line)."""

    text = (generated or "").lower()
    return any(p in text for p in NO_INFO_PHRASES)


def retrieval_hit(documents: list[dict], expected_source: str | None) -> bool | None:
    """
    Whether the expected source document appears anywhere among the
    (already reranked, top-k) retrieved documents. Returns None if the
    golden item has no expected_source (not applicable).
    """

    if not expected_source:
        return None

    retrieved_sources = {doc.get("document_name") for doc in documents}
    return expected_source in retrieved_sources


def aggregate_report(results: list[dict]) -> dict:
    """
    Rolls up per-item eval results into summary metrics.

    Confidence-calibration metrics deserve a note:
      - false_escalation_rate: of the items the confidence score flagged
        for escalation, what fraction would actually have been answered
        correctly? High values mean the threshold is too conservative
        (customers get bounced to a human unnecessarily).
      - missed_escalation_rate: of the items the system got wrong, what
        fraction were NOT escalated (i.e. a wrong answer was shown to the
        customer with no human safety net)? This is the more dangerous
        failure mode and the one worth watching most closely.
    """

    total = len(results)

    factual = [r for r in results if r["question_type"] == "factual"]
    open_ended = [r for r in results if r["question_type"] == "open_ended"]
    out_of_scope = [r for r in results if r["question_type"] == "out_of_scope"]

    overall_accuracy = (
        sum(r["is_correct"] for r in results) / total if total else None
    )
    out_of_scope_accuracy = (
        sum(r["is_correct"] for r in out_of_scope) / len(out_of_scope)
        if out_of_scope else None
    )

    per_difficulty: dict[str, dict[str, int]] = {}
    for r in results:
        bucket = per_difficulty.setdefault(
            r.get("difficulty", "easy"), {"total": 0, "correct": 0}
        )
        bucket["total"] += 1
        if r["is_correct"]:
            bucket["correct"] += 1

    retrieval_hits = [
        r["retrieval_hit"] for r in results if r["retrieval_hit"] is not None
    ]
    retrieval_hit_rate = (
        sum(retrieval_hits) / len(retrieval_hits) if retrieval_hits else None
    )

    chunk_rows = [r for r in results if r.get("chunk_hit") is not None]
    chunk_hit_rate = (
        sum(r["chunk_hit"] for r in chunk_rows) / len(chunk_rows) if chunk_rows else None
    )
    chunk_hit_at_1 = (
        sum(r.get("chunk_rank") == 1 for r in chunk_rows) / len(chunk_rows) if chunk_rows else None
    )
    chunk_mrr = mean(r["chunk_rr"] for r in chunk_rows) if chunk_rows else None

    factual_correct = [r["is_correct"] for r in factual]
    factual_accuracy = (
        sum(factual_correct) / len(factual_correct) if factual_correct else None
    )

    judge_scores = [
        r["judge_score"] for r in open_ended if r.get("judge_score") is not None
    ]
    avg_judge_score = mean(judge_scores) if judge_scores else None

    confidences = [r["confidence"] for r in results]
    avg_confidence = mean(confidences) if confidences else 0.0

    # Escalation metrics are about questions the bot is *supposed* to
    # answer; out-of-scope questions are scored separately above.
    answerable = [r for r in results if r["question_type"] != "out_of_scope"]
    escalated = [r for r in answerable if r["would_escalate"]]
    escalation_rate = len(escalated) / len(answerable) if answerable else 0.0

    correct_but_escalated = [r for r in escalated if r["is_correct"]]
    false_escalation_rate = (
        len(correct_but_escalated) / len(escalated) if escalated else 0.0
    )

    incorrect_total = [r for r in answerable if not r["is_correct"]]
    incorrect_and_not_escalated = [
        r for r in incorrect_total if not r["would_escalate"]
    ]
    missed_escalation_rate = (
        len(incorrect_and_not_escalated) / len(incorrect_total)
        if incorrect_total else 0.0
    )

    per_category: dict[str, dict[str, int]] = {}
    for r in results:
        cat = r["category"]
        bucket = per_category.setdefault(cat, {"total": 0, "correct": 0})
        bucket["total"] += 1
        if r["is_correct"]:
            bucket["correct"] += 1

    avg_retrieval_time_s = mean(r["retrieval_time_s"] for r in results) if results else 0.0
    avg_generation_time_s = mean(r["generation_time_s"] for r in results) if results else 0.0

    return {
        "total_items": total,
        "overall_accuracy": overall_accuracy,
        "out_of_scope_accuracy": out_of_scope_accuracy,
        "out_of_scope_count": len(out_of_scope),
        "per_difficulty": per_difficulty,
        "retrieval_hit_rate": retrieval_hit_rate,
        "chunk_hit_rate": chunk_hit_rate,
        "chunk_hit_at_1": chunk_hit_at_1,
        "chunk_mrr": chunk_mrr,
        "factual_accuracy": factual_accuracy,
        "factual_count": len(factual),
        "avg_judge_score": avg_judge_score,
        "open_ended_count": len(open_ended),
        "avg_confidence": avg_confidence,
        "escalation_rate": escalation_rate,
        "false_escalation_rate": false_escalation_rate,
        "missed_escalation_rate": missed_escalation_rate,
        "incorrect_count": len(incorrect_total),
        "per_category": per_category,
        "avg_retrieval_time_s": avg_retrieval_time_s,
        "avg_generation_time_s": avg_generation_time_s,
    }


if __name__ == "__main__":
    # Tiny smoke test you can run standalone: `python -m evaluation.metrics`
    assert contains_answer("The link is valid for 15 minutes.", "15 minutes")
    assert contains_answer("Refunds take 3 to 5 business days.", "3-5 business days")
    assert not contains_answer("I'm not sure.", "15 minutes")
    assert retrieval_hit(
        [{"document_name": "Warranty_Policy.pdf"}], "Warranty_Policy.pdf"
    ) is True
    assert retrieval_hit(
        [{"document_name": "Other.pdf"}], "Warranty_Policy.pdf"
    ) is False
    assert retrieval_hit([{"document_name": "Other.pdf"}], None) is None
    print("metrics.py smoke tests passed.")
