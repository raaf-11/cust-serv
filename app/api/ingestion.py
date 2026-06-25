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

    files = [
        "data/Password_Reset_and_Account_Security.pdf",
        "data/Mobile_Phone_User_Manual.pdf",
        "data/Laptop_Troubleshooting_Guide.pdf",
        "data/Warranty_Policy.pdf",
        "data/Employee_Handbook.pdf",
        "data/Complaint_Resolution_Guide.pdf",
        "data/Refund_and_Return_Policy.pdf",
        "data/Shipping_and_Delivery_Policy.pdf"
    ]

    for file in files:

        ingestion_service.ingest_file(
            file_path=file,
            source_type="pdf"
        )

    return {
        "message": "Knowledge base loaded successfully."
    }