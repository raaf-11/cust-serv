class ConfidenceService:

    def __init__(self, threshold: float = 0.60):
        self.threshold = threshold

    def calculate_confidence(
        self,
        documents: list[dict]
    ) -> float:

        if not documents:
            return 0.0

        # -------------------------------------------------
        # 1. RERANKER CONSISTENCY
        # -------------------------------------------------

        rerank_scores = [
            document.get("rerank_score")
            for document in documents
            if document.get("rerank_score") is not None
        ]

        if not rerank_scores:
            return 0.0

        # Reranked results are already sorted.
        best_rerank = rerank_scores[0]

        # Difference between best and second best.
        if len(rerank_scores) > 1:
            score_gap = best_rerank - rerank_scores[1]
        else:
            score_gap = 0.0

        # Normalize the ranking gap.
        #
        # A gap of ~2 or more means the top result is
        # substantially stronger than the second result.
        gap_score = min(score_gap / 2.0, 1.0)

        # -------------------------------------------------
        # 2. SOURCE AGREEMENT
        # -------------------------------------------------

        top_source = documents[0].get("document_name")

        same_source_count = sum(
            1
            for document in documents
            if document.get("document_name") == top_source
        )

        source_agreement = (
            same_source_count / len(documents)
        )

        # -------------------------------------------------
        # 3. VECTOR RELEVANCE
        # -------------------------------------------------

        vector_scores = [
            document.get("vector_score")
            for document in documents
            if document.get("vector_score") is not None
        ]

        if vector_scores:
            best_vector_score = max(vector_scores)

            # Qdrant cosine similarity is approximately
            # in the 0-1 range for our embeddings.
            vector_relevance = max(
                0.0,
                min(best_vector_score, 1.0)
            )
        else:
            vector_relevance = 0.0

        # -------------------------------------------------
        # 4. FINAL CONFIDENCE
        # -------------------------------------------------

        confidence = (
            0.50 * vector_relevance
            + 0.30 * source_agreement
            + 0.20 * gap_score
        )

        return round(confidence, 4)

    def should_escalate(
        self,
        confidence_score: float
    ) -> bool:

        return confidence_score < self.threshold


confidence_service = ConfidenceService()