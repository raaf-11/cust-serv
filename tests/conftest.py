import pytest

from app.core.config import settings


def _services_reachable() -> bool:
    try:
        from qdrant_client import QdrantClient
        QdrantClient(url=settings.QDRANT_URL).get_collections()
    except Exception:
        return False

    try:
        from elasticsearch import Elasticsearch
        es = Elasticsearch(settings.ELASTICSEARCH_URL)
        if not es.ping():
            return False
    except Exception:
        return False

    return True


@pytest.fixture(scope="session")
def require_live_services():
    """
    Skips (rather than errors) eval tests when Qdrant/Elasticsearch aren't
    reachable, e.g. in a CI job that doesn't spin up the full stack.
    """

    if not _services_reachable():
        pytest.skip(
            "Qdrant and/or Elasticsearch are not reachable. Start the "
            "backing services and ingest the knowledge base (see "
            "evaluation/README.md) before running eval tests."
        )
