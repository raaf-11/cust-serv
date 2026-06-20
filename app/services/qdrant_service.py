from qdrant_client import QdrantClient

from app.core.config import settings


class QdrantService:

    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL
        )

    def get_collections(self):
        return self.client.get_collections()


qdrant_service = QdrantService()