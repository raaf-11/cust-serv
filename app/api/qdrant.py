from fastapi import APIRouter

from app.services.qdrant_service import (
    qdrant_service
)

router = APIRouter(
    prefix="/qdrant",
    tags=["Qdrant"]
)


@router.get("/collections")
def get_collections():
    return qdrant_service.get_collections()