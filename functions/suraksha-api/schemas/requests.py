from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or employee ID")
    password_hash: str = Field(..., description="SHA-256 hashed password")

class ChatQueryRequest(BaseModel):
    session_id: str = Field(..., description="Unique chat session identifier")
    message: str = Field(..., description="User's natural language query")
