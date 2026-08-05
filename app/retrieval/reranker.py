from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    """
    Re-ranks retrieved documents using a CrossEncoder.

    The CrossEncoder jointly encodes the query and document,
    producing a relevance score.
    """

    def __init__(self):

        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 5
    ) -> list[dict]:

        if not documents:
            return []

        sentence_pairs = [
            (query, document["text"])
            for document in documents
        ]

        scores = self.model.predict(
            sentence_pairs
        )

        reranked = []

        for document, score in zip(
            documents,
            scores
        ):

            document = document.copy()

            document["rerank_score"] = float(score)

            reranked.append(document)

        reranked.sort(
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        return reranked[:top_k]


reranker = CrossEncoderReranker()