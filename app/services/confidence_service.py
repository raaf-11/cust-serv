"""
Retrieval confidence: "did we find a passage that actually answers this?"

What was wrong with the old formula
-----------------------------------
    0.50 * best vector score
  + 0.30 * share of top-5 chunks from the same PDF
  + 0.20 * gap between the 1st and 2nd rerank score

* MiniLM cosine scores for a short question vs a 500-char chunk usually sit
  around 0.35-0.65, so the biggest term was always "half confident".
* "Same PDF" punished good answers: a question about refunds for a damaged
  laptop legitimately pulls chunks from Refund, Warranty and Laptop docs.
* The rank gap punished the BEST case: when two chunks both contain the
  answer (very common with 100-char chunk overlap) the gap is ~0.
* It never used the absolute cross-encoder score, which is the one signal
  that is trained to answer "is this passage relevant to this question?".

Net effect: perfectly answerable questions landed around 0.35-0.45, right on
top of the 0.40 threshold, so the tiniest change (a typo, a different word)
flipped the decision.

New formula
-----------
The cross-encoder (ms-marco-MiniLM-L-6-v2) outputs a logit: clearly relevant
passages score well above 0, unrelated ones around -8 to -11. We squash it to
0..1 and blend in a little of the vector score as a safety net.

    confidence = 0.75 * sigmoid(best_rerank / 2) + 0.25 * vector_term

Rough guide:
    on-topic question             -> 0.8 - 1.0
    vague / partially covered     -> 0.3 - 0.6   (still answered)
    nothing relevant in the KB    -> < 0.15

Run `python -m evaluation.calibrate_escalation` to see the real numbers for
your data and tune CONFIDENCE_THRESHOLD in .env if needed.
"""

import math
import os

DEFAULT_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))

RERANK_WEIGHT = 0.75
VECTOR_WEIGHT = 0.25

# Cosine similarity below this is noise for all-MiniLM-L6-v2; above the
# upper bound we treat it as a full match.
VECTOR_FLOOR = 0.15
VECTOR_CEILING = 0.60


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


class ConfidenceService:

    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        self.threshold = threshold

    def calculate_confidence(
        self,
        documents: list[dict]
    ) -> float:

        if not documents:
            return 0.0

        rerank_scores = [
            d["rerank_score"]
            for d in documents
            if d.get("rerank_score") is not None
        ]

        vector_scores = [
            d["vector_score"]
            for d in documents
            if d.get("vector_score") is not None
        ]

        if not rerank_scores and not vector_scores:
            return 0.0

        # 1. Cross-encoder relevance of the best passage (main signal).
        #    Dividing by 2 softens the curve: logit 0 -> 0.5,
        #    +4 -> 0.88, -4 -> 0.12.
        if rerank_scores:
            rerank_term = _sigmoid(max(rerank_scores) / 2.0)
        else:
            rerank_term = 0.0

        # 2. Semantic similarity of the best passage (safety net).
        if vector_scores:
            best_vector = max(vector_scores)
            vector_term = (best_vector - VECTOR_FLOOR) / (
                VECTOR_CEILING - VECTOR_FLOOR
            )
            vector_term = max(0.0, min(vector_term, 1.0))
        else:
            vector_term = 0.0

        if not rerank_scores:
            return round(vector_term, 4)

        confidence = (
            RERANK_WEIGHT * rerank_term
            + VECTOR_WEIGHT * vector_term
        )

        return round(confidence, 4)

    def should_escalate(
        self,
        confidence_score: float
    ) -> bool:
        """
        True when retrieval found nothing usable. Note this no longer
        creates a ticket by itself: ChatService first asks the user to
        rephrase, and only escalates if it happens again (see
        escalation_policy.py).
        """

        return confidence_score < self.threshold


def _configured_threshold() -> float:
    try:
        from app.core.config import settings
        return settings.CONFIDENCE_THRESHOLD
    except Exception:
        return DEFAULT_THRESHOLD


confidence_service = ConfidenceService(threshold=_configured_threshold())
