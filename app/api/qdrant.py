from fastapi import APIRouter

from app.services.qdrant_service import (
    qdrant_service
)
from app.services.embedding_service import (
    embedding_service
)

router = APIRouter(
    prefix="/qdrant",
    tags=["Qdrant"]
)


@router.get("/collections")
def get_collections():
    return qdrant_service.get_collections()


@router.post("/create-collection")
def create_collection():

    qdrant_service.create_collection()

    return {
        "message": "Collection created successfully."
    }

@router.post("/store-test-point")
def store_test_point():

    text = "Employees receive 20 vacation days annually."

    vector = embedding_service.embed(
        text
    )

    payload = {
        "text": text,
        "document_name": "employee_handbook.pdf",
        "chunk_index": 1,
        "source_type": "policy"
    }

    point_id = qdrant_service.store_point(
        vector=vector,
        payload=payload
    )

    return {
        "point_id": point_id
    }

@router.get("/search-test")
def search_test():

    query = "How many vacation days do I get?"

    query_vector = embedding_service.embed(
        query
    )

    results = qdrant_service.search(
        query_vector=query_vector
    )

    return results