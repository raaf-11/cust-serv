import math
import os

DEFAULT_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))

RERANK_WEIGHT = 0.75
VECTOR_WEIGHT = 0.25

VECTOR_FLOOR = 0.15
VECTOR_CEILING = 0.60


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


class ConfidenceService:
    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        self.threshold = threshold

    def calculate_confidence(self, documents: list[dict]) -> float:
        if not documents:
            return 0.0

        rerank_scores = [
            d["rerank_score"] for d in documents if d.get("rerank_score") is not None
        ]

        vector_scores = [
            d["vector_score"] for d in documents if d.get("vector_score") is not None
        ]

        if not rerank_scores and not vector_scores:
            return 0.0

        if rerank_scores:
            rerank_term = _sigmoid(max(rerank_scores) / 2.0)
        else:
            rerank_term = 0.0

        if vector_scores:
            best_vector = max(vector_scores)
            vector_term = (best_vector - VECTOR_FLOOR) / (VECTOR_CEILING - VECTOR_FLOOR)
            vector_term = max(0.0, min(vector_term, 1.0))
        else:
            vector_term = 0.0

        if not rerank_scores:
            return round(vector_term, 4)

        confidence = RERANK_WEIGHT * rerank_term + VECTOR_WEIGHT * vector_term
        return round(confidence, 4)

    def should_escalate(self, confidence_score: float) -> bool:
        return confidence_score < self.threshold


def _configured_threshold() -> float:
    try:
        from app.core.config import settings

        return settings.CONFIDENCE_THRESHOLD
    except Exception:
        return DEFAULT_THRESHOLD


confidence_service = ConfidenceService(threshold=_configured_threshold())
