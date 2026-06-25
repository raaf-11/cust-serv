from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: int
    message: str = Field(
        ...,
        min_length=1
    )


class ChatResponse(BaseModel):
    answer: str