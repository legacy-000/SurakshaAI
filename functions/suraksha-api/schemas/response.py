from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class APIResponse(BaseModel):
    """
    Standard API Response envelope for SURAKSHA AI.
    """
    status: str = Field(..., description="Response status (e.g., 'success', 'error', 'Project Initialized')")
    message: str = Field(..., description="Human-readable response message")
    error_code: Optional[str] = Field(None, alias="errorCode", description="System error code if status is error")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the response")
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="traceId", description="Unique identifier for request tracing")
    data: Optional[Any] = Field(None, description="Response payload")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed successfully",
                "errorCode": None,
                "timestamp": "2026-06-30T17:42:00Z",
                "traceId": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                "data": {
                    "status": "Project Initialized"
                }
            }
        }
StandardResponse = APIResponse
