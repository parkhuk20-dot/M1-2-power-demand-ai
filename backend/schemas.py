from datetime import date as date_type

from pydantic import BaseModel, Field, field_validator


class DataCreate(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    value: float
    memo: str = ""

    @field_validator("date")
    @classmethod
    def valid_date(cls, v: str) -> str:
        date_type.fromisoformat(v)
        return v


class DataUpdate(BaseModel):
    date: str | None = None
    value: float | None = None
    memo: str | None = None

    @field_validator("date")
    @classmethod
    def valid_date(cls, v: str | None) -> str | None:
        if v is not None:
            date_type.fromisoformat(v)
        return v


class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    messages: list[Message]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = None
