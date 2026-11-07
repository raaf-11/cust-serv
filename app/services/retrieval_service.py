from app.retrieval.hybrid_retriever import hybrid_retriever
from app.utils.retrieval_debugger import RetrievalDebugger
from app.services.elasticsearch_service import elasticsearch_service
from app.services.query_normalizer import QueryNormalizer


def _english_words():
    from app.services.embedding_service import embedding_service

    vocab = embedding_service.model.tokenizer.get_vocab()
    return [w for w in vocab if w.isalpha()]


query_normalizer = QueryNormalizer(
    text_loader=elasticsearch_service.get_all_texts,
    english_words_loader=_english_words,
)


class RetrievalService:
    def retrieve(
        self, question: str, candidate_count: int = 20, final_count: int = 5
    ) -> dict:
        search_query = query_normalizer.normalize(question)

        if search_query != question:
            print(f"QUERY NORMALIZED: {question!r} -> {search_query!r}")

        retrieved_documents = hybrid_retriever.retrieve(
            query=search_query, candidate_count=candidate_count, final_count=final_count
        )

        chunks = [document["text"] for document in retrieved_documents]
        context = "\n\n".join(chunks)

        return {
            "context": context,
            "documents": retrieved_documents,
            "search_query": search_query,
        }


retrieval_service = RetrievalService()
