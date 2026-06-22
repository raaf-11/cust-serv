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

    ingestion_service.ingest_file(
        "data/Employee Handbook and Company Policies.txt",
        source_type="policy"
    )

    ingestion_service.ingest_file(
        "data/Customer Complaint Resolution Guide.txt",
        source_type="complaint"
    )

    ingestion_service.ingest_file(
        "data/Customer Account and Security Help.txt",
        source_type="customer_help"
    )

    return {
        "message": "Knowledge base loaded successfully."
    }