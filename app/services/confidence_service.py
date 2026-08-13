class ConfidenceService:

    def __init__(self, threshold: float = 0.60):
        self.threshold = threshold

    def calculate_confidence(
        self,
        documents: list[dict]
    ) -> float:
        """
        Calculates a confidence score based on the
        CrossEncoder reranker scores.

        The score is normalized to a 0-1 range using
        a sigmoid transformation.
        """

        if not documents:
            return 0.0

        rerank_scores = [
            document.get("rerank_score")
            for document in documents
            if document.get("rerank_score") is not None
        ]

        if not rerank_scores:
            return 0.0

        # Use the strongest retrieved document as the
        # primary relevance signal.
        best_score = max(rerank_scores)

        # Normalize CrossEncoder score to approximately 0-1.
        confidence = 1 / (1 + pow(2.71828, -best_score))

        return round(confidence, 4)

    def should_escalate(
        self,
        confidence_score: float
    ) -> bool:
        """
        Determines whether the conversation should
        be escalated to a human agent.
        """

        return confidence_score < self.threshold


confidence_service = ConfidenceService()