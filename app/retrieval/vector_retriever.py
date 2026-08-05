from app.services.embedding_service import (
    embedding_service
)

from app.services.qdrant_service import (
    qdrant_service
)


class VectorRetriever:
    """
    Performs semantic retrieval using Qdrant.
    """

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> list[dict]:

        query_vector = embedding_service.embed(
            query
        )

        results = qdrant_service.search(
            query_vector=query_vector,
            limit=top_k
        )

        retrieved = []

        for point in results:

            payload = point.payload.copy()

            payload["vector_score"] = point.score

            retrieved.append(payload)

        return retrieved


vector_retriever = VectorRetriever()