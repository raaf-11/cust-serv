from app.retrieval.vector_retriever import vector_retriever
from app.retrieval.keyword_retriever import keyword_retriever
from app.retrieval.merge import merge_results
from app.retrieval.reranker import reranker
from app.utils.retrieval_debugger import RetrievalDebugger


class HybridRetriever:

    def retrieve(
        self,
        query: str,
        candidate_count: int = 20,
        final_count: int = 5
    ) -> list[dict]:

        RetrievalDebugger.print_query(query)

        vector_results = vector_retriever.retrieve(
            query=query,
            top_k=candidate_count
        )

        RetrievalDebugger.print_vector_results(
            vector_results
        )

        keyword_results = keyword_retriever.retrieve(
            query=query,
            top_k=candidate_count
        )

        RetrievalDebugger.print_keyword_results(
            keyword_results
        )

        merged = merge_results.merge(
            vector_results,
            keyword_results
        )

        RetrievalDebugger.print_merged_results(
            merged
        )

        reranked = reranker.rerank(
            query=query,
            documents=merged,
            top_k=final_count
        )

        RetrievalDebugger.print_reranked_results(
            reranked
        )

        return reranked


hybrid_retriever = HybridRetriever()