from datetime import datetime

from pydantic import BaseModel


class ConversationResponse(BaseModel):
    id: int
    message: str
    answer: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }