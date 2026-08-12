from app.retrieval.hybrid_retriever import hybrid_retriever
from app.utils.retrieval_debugger import RetrievalDebugger


class RetrievalService:

    def retrieve(
        self,
        question: str,
        candidate_count: int = 20,
        final_count: int = 5
    ) -> dict:
        """
        Retrieves the most relevant context for the user's question
        using Hybrid RAG.

        Returns both:
        1. Combined text context for the LLM
        2. Retrieval metadata and scores for confidence evaluation
        """

        retrieved_documents = hybrid_retriever.retrieve(
            query=question,
            candidate_count=candidate_count,
            final_count=final_count
        )

        chunks = [
            document["text"]
            for document in retrieved_documents
        ]

        context = "\n\n".join(chunks)

        RetrievalDebugger.print_context(context)

        return {
            "context": context,
            "documents": retrieved_documents
        }


retrieval_service = RetrievalService()