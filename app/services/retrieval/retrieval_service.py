from app.services.embedding_service import (
    embedding_service
)

from app.services.qdrant_service import (
    qdrant_service
)


class RetrievalService:

    def retrieve(
        self,
        question: str,
        limit: int = 5
    ) -> str:

        query_vector = embedding_service.embed(
            question
        )

        results = qdrant_service.search(
            query_vector=query_vector,
            limit=limit
        )

        chunks = []

        for point in results:

            chunks.append(
                point.payload["text"]
            )

        context = "\n\n".join(
            chunks
        )

        return context


retrieval_service = RetrievalService()