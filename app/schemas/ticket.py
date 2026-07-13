from datetime import datetime
from pydantic import BaseModel, Field


class TicketCreate(BaseModel):

    session_id: int

    subject: str = Field(
        ...,
        min_length=3,
        max_length=100
    )

    description: str = Field(
        ...,
        min_length=10
    )

class TicketResponse(BaseModel):

    id: int

    subject: str

    description: str

    status: str

    created_at: datetime

    model_config = {
        "from_attributes": True
    }