from pydantic import BaseModel, Field


class EmployeeMessageRequest(BaseModel):

    message: str = Field(
        ...,
        min_length=1
    )