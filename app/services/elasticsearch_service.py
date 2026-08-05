from elasticsearch import Elasticsearch
from app.core.config import settings


class ElasticsearchService:

    def __init__(self):
        print("ES URL:", settings.ELASTICSEARCH_URL)
        print("ES INDEX:", repr(settings.ELASTICSEARCH_INDEX))

        self.client = Elasticsearch(settings.ELASTICSEARCH_URL)
        self.index_name = settings.ELASTICSEARCH_INDEX

        self.create_index()

    def create_index(self):
        try:
            if self.client.indices.exists(index=self.index_name):
                return

            mapping = {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "text": {"type": "text"},
                        "document_name": {"type": "keyword"},
                        "chunk_index": {"type": "integer"},
                        "source_type": {"type": "keyword"}
                    }
                }
            }

            self.client.indices.create(
                index=self.index_name,
                body=mapping
            )

            print(f"Created Elasticsearch index: {self.index_name}")

        except Exception as e:
            print("Elasticsearch Exception:", repr(e))
            raise

    def index_chunk(self, payload: dict):
        """
        Index a single chunk.
        """

        self.client.index(
            index=self.index_name,
            id=payload["id"],
            document=payload
        )

    def index_chunks(self, payloads: list[dict]):
        """
        Index multiple chunks.
        """

        operations = []

        for payload in payloads:

            operations.append(
                {
                    "index": {
                        "_index": self.index_name,
                        "_id": payload["id"]
                    }
                }
            )

            operations.append(payload)

        self.client.bulk(
            operations=operations,
            refresh=True
        )

    def keyword_search(
        self,
        query: str,
        limit: int = 5
    ) -> list[dict]:
        """
        Perform BM25 keyword search.
        """

        response = self.client.search(
            index=self.index_name,
            size=limit,
            query={
                "match": {
                    "text": query
                }
            }
        )

        results = []

        for hit in response["hits"]["hits"]:

            payload = hit["_source"].copy()

            payload["bm25_score"] = hit["_score"]

            results.append(payload)

        return results

    def delete_index(self):

        if self.client.indices.exists(index=self.index_name):

            self.client.indices.delete(
                index=self.index_name
            )

            print(f"Deleted index: {self.index_name}")

    def get_document_count(self):

        response = self.client.count(
            index=self.index_name
        )

        return response["count"]

    def health_check(self):

        return self.client.ping()


elasticsearch_service = ElasticsearchService()