from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, Any

T = TypeVar('T')

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict = Field(default_factory=dict, description="Additional error details")

class APIResponse(BaseModel, Generic[T]):
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data")
    error: Optional[ErrorDetail] = Field(None, description="Error information")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "id": 1,
                    "title": "Backend Dev"
                },
                "error": None
            }
        }

