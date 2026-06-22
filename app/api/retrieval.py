from fastapi import APIRouter

from app.services.retrieval_service import (
    retrieval_service
)

router = APIRouter(
    prefix="/retrieval",
    tags=["Retrieval"]
)


@router.get("/test")
def test_retrieval():

    context = retrieval_service.retrieve(
        "How do I reset my password?"
    )

    return {
        "context": context
    }