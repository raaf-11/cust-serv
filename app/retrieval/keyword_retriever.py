from app.services.elasticsearch_service import elasticsearch_service


class KeywordRetriever:
    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        results = elasticsearch_service.keyword_search(query=query, limit=top_k)
        return results


keyword_retriever = KeywordRetriever()
