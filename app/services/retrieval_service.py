from app.retrieval.hybrid_retriever import hybrid_retriever
from app.utils.retrieval_debugger import RetrievalDebugger
from app.services.elasticsearch_service import elasticsearch_service
from app.services.query_normalizer import QueryNormalizer

# Vocabulary is loaded lazily from Elasticsearch on the first query.
query_normalizer = QueryNormalizer(
    text_loader=elasticsearch_service.get_all_texts
)


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

        # Fix typos ("laptp" -> "laptop") before searching. The original
        # question is still what the LLM sees and what gets stored.
        search_query = query_normalizer.normalize(question)

        if search_query != question:
            print(f"QUERY NORMALIZED: {question!r} -> {search_query!r}")

        retrieved_documents = hybrid_retriever.retrieve(
            query=search_query,
            candidate_count=candidate_count,
            final_count=final_count
        )

        chunks = [
            document["text"]
            for document in retrieved_documents
        ]

        context = "\n\n".join(chunks)

        #RetrievalDebugger.print_context(context)

        return {
            "context": context,
            "documents": retrieved_documents,
            "search_query": search_query
        }


retrieval_service = RetrievalService()