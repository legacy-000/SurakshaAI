from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None
    language: str | None = None   # en | kn | auto


class LoginRequest(BaseModel):
    username: str
    password: str
