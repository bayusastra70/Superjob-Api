from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List
import uuid

class CompanyReviewBase(BaseModel):
    id: uuid.UUID = Field(..., description="The ID of the company review")
    company_id: uuid.UUID = Field(..., description="The ID of the company")
    user_id: int = Field(..., description="The ID of the user")
    title: str = Field(..., description="The title of the company review")
    pros: str = Field(..., description="The pros of the company review")
    cons: str = Field(..., description="The cons of the company review")
    position: str = Field(..., description="The position of the company review")
    employment_status: str = Field(..., description="The employment status of the company review")
    employment_duration: str = Field(..., description="The employment duration of the company review")
    rating: int = Field(..., description="The rating of the company review")

    class Config:
        orm_mode = True

class CompanyReviewCreate(CompanyReviewBase):
    created_at: datetime = Field(..., description="The date and time the company review was created")

class CompanyReviewUpdate(CompanyReviewBase):
    updated_at: datetime = Field(..., description="The date and time the company review was last updated")

class CompanyReviewResponse(CompanyReviewBase):
    created_at: datetime = Field(..., description="The date and time the company review was created")
    updated_at: datetime = Field(..., description="The date and time the company review was last updated")


class Pagination(BaseModel):
    page: int
    limit: int
    total_pages: int


class ReviewSummary(BaseModel):
    average_rating: float
    total_reviews: int
    rating_breakdown: Dict[str, int]


class CompanyReviewsResponse(BaseModel):
    company_id: uuid.UUID
    pagination: Pagination
    summary: ReviewSummary
    reviews: List[CompanyReviewResponse]

    class Config:
        orm_mode = True

class CompanyRatingSummaryResponse(BaseModel):
    rating: float
    total_reviews: int