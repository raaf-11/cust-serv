from datetime import datetime

from pydantic import BaseModel


class SessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }