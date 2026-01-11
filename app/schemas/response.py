
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    code: int = Field(..., description="HTTP Status Code")
    isSuccess: bool = Field(..., description="Success indicator")
    message: str = Field(..., description="Response message")
    data: Optional[T] = Field(None, description="Response data")




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