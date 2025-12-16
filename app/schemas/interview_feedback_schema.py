import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class InterviewFeedbackBase(BaseModel):
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating 1-5",
        json_schema_extra={"error_messages": {"required": "Rating wajib diisi"}},
    )
    feedback: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional feedback, minimum 10 characters if provided",
    )

    @field_validator("feedback")
    @classmethod
    def validate_feedback_min_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() != "" and len(v) < 10:
            raise ValueError("Feedback minimal 10 karakter")
        if v is not None and len(v) > 500:
            raise ValueError("Feedback maksimal 500 karakter")
        # Jika empty string, convert ke None
        if v is not None and v.strip() == "":
            return None
        return v


class InterviewFeedbackCreate(InterviewFeedbackBase):
    application_id: int = Field(..., description="Application ID")


class InterviewFeedbackUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating 1-5")
    feedback: Optional[str] = Field(None, max_length=500)

    @field_validator("feedback")
    @classmethod
    def validate_feedback_min_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() != "" and len(v) < 10:
            raise ValueError("Feedback minimal 10 karakter")
        if v is not None and len(v) > 500:
            raise ValueError("Feedback maksimal 500 karakter")
        if v is not None and v.strip() == "":
            return None
        return v


class InterviewFeedbackResponse(InterviewFeedbackBase):
    id: uuid.UUID
    application_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterviewFeedbackOptionalResponse(BaseModel):
    """Response yang bisa kosong jika feedback belum ada"""

    id: Optional[uuid.UUID] = None
    application_id: Optional[int] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    exists: bool = False  # Flag untuk indicate apakah data ada atau tidak

    class Config:
        from_attributes = True

    @classmethod
    def empty(
        cls, application_id: Optional[int] = None
    ) -> "InterviewFeedbackOptionalResponse":
        """Factory method untuk create empty response"""
        return cls(
            id=None,
            application_id=application_id,
            rating=None,
            feedback=None,
            created_by=None,
            created_at=None,
            updated_at=None,
            exists=False,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "InterviewFeedbackOptionalResponse":
        """Factory method untuk create response dari dict"""
        return cls(
            id=data.get("id"),
            application_id=data.get("application_id"),
            rating=data.get("rating"),
            feedback=data.get("feedback"),
            created_by=data.get("created_by"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            exists=True,
        )
