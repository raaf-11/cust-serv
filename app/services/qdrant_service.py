import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

from app.core.config import settings

class QdrantService:

    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL
        )

    def get_collections(self):
        return self.client.get_collections()

    def create_collection(self):

        collections = self.client.get_collections()

        existing_collections = [
            collection.name
            for collection in collections.collections
        ]

        if settings.QDRANT_COLLECTION_NAME in existing_collections:
            return

        self.client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIMENSION,
                distance=Distance.COSINE
            )
        )

    def store_point(
        self,
        vector: list[float],
        payload: dict
    ) -> str:

        point_id = str(uuid.uuid4())

        self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )

        return point_id

    def store_points(
        self,
        vectors: list[list[float]],
        payloads: list[dict]
    ):

        points = []

        for vector, payload in zip(vectors, payloads):

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=payload
                )
            )

        self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=points
        )

    def search(
        self,
        query_vector: list[float],
        limit: int = 5
    ):

        results = self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query=query_vector,
            limit=limit
        )

        return results.points
    

    def delete_collection(self):

        self.client.delete_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME
        )
    


qdrant_service = QdrantService()