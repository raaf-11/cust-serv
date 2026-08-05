from app.core.config import settings


class RetrievalDebugger:

    @staticmethod
    def print_query(query: str):

        if not settings.DEBUG_RETRIEVAL:
            return

        print("\n" + "=" * 80)
        print("QUERY")
        print("=" * 80)
        print(query)

    @staticmethod
    def print_vector_results(results):

        if not settings.DEBUG_RETRIEVAL:
            return

        print("\n" + "=" * 80)
        print("VECTOR SEARCH RESULTS")
        print("=" * 80)

        for i, doc in enumerate(results, start=1):

            print(
                f"{i}. "
                f"{doc['document_name']} | "
                f"Chunk {doc['chunk_index']} | "
                f"Score={doc.get('vector_score', 0):.4f}"
            )

    @staticmethod
    def print_keyword_results(results):

        if not settings.DEBUG_RETRIEVAL:
            return

        print("\n" + "=" * 80)
        print("BM25 SEARCH RESULTS")
        print("=" * 80)

        for i, doc in enumerate(results, start=1):

            print(
                f"{i}. "
                f"{doc['document_name']} | "
                f"Chunk {doc['chunk_index']} | "
                f"Score={doc.get('bm25_score', 0):.4f}"
            )

    @staticmethod
    def print_merged_results(results):

        if not settings.DEBUG_RETRIEVAL:
            return

        print("\n" + "=" * 80)
        print(f"MERGED RESULTS ({len(results)} candidates)")
        print("=" * 80)

        for i, doc in enumerate(results, start=1):

            print(
                f"{i}. "
                f"{doc['document_name']} | "
                f"Chunk {doc['chunk_index']} | "
                f"Vector={doc.get('vector_score')} | "
                f"BM25={doc.get('bm25_score')}"
            )

    @staticmethod
    def print_reranked_results(results):

        if not settings.DEBUG_RETRIEVAL:
            return

        print("\n" + "=" * 80)
        print("RERANKED RESULTS")
        print("=" * 80)

        for i, doc in enumerate(results, start=1):

            print(
                f"{i}. "
                f"{doc['document_name']} | "
                f"Chunk {doc['chunk_index']} | "
                f"Rerank={doc['rerank_score']:.4f}"
            )

    @staticmethod
    def print_context(context: str):

        if not settings.DEBUG_RETRIEVAL:
            return

        print("\n" + "=" * 80)
        print("FINAL CONTEXT SENT TO LLM")
        print("=" * 80)
        print(context)
        print("=" * 80)