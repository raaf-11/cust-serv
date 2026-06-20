from fastapi import APIRouter

from app.services.embedding_service import (
    embedding_service
)

router = APIRouter(
    prefix="/embedding",
    tags=["Embedding"]
)


@router.get("/test")
def test_embedding():

    vector = embedding_service.embed(
        "Hello World"
    )

    return {
        "dimension": len(vector)
    }