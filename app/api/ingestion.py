from fastapi import APIRouter

from app.services.ingestion_service import (
    ingestion_service
)

router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"]
)


@router.post("/load-test-data")
def load_test_data():

    ingestion_service.ingest_file("data/company_handbook.pdf")

    return {"message": "Knowledge base loaded successfully."}