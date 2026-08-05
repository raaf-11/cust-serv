from fastapi import APIRouter
from app.services.elasticsearch_service import elasticsearch_service

router = APIRouter(
    prefix="/elasticsearch",
    tags=["ElasiticSearch"]
)

@router.delete("/index")
def delete_index():
    elasticsearch_service.delete_index()
    return {"message": "Elasticsearch index deleted successfully."}