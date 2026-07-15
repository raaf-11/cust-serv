from datetime import datetime

from pydantic import BaseModel


class ConversationResponse(BaseModel):

    id: int

    session_id: int

    sender: str

    content: str

    created_at: datetime

    model_config = {
        "from_attributes": True
    }