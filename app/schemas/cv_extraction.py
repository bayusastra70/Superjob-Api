from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProfileData(BaseModel):
    full_name: Optional[str] = Field(None, description="Full name of the candidate")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="City or country location")
    summary: Optional[str] = Field(None, description="Professional summary or bio")


class WorkExperience(BaseModel):
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Job position or title")
    duration: str = Field(
        ..., description="Duration (e.g., 2020-Present or Jan 2020 - Dec 2022)"
    )
    description: Optional[str] = Field(
        None, description="Job responsibilities and achievements"
    )


class Education(BaseModel):
    institution: str = Field(..., description="School or university name")
    degree: str = Field(..., description="Degree (e.g., Bachelor, Master, PhD)")
    field: Optional[str] = Field(
        None, description="Field of study (e.g., Computer Science)"
    )
    year: Optional[str] = Field(None, description="Graduation year or duration")


class Certification(BaseModel):
    name: str = Field(..., description="Certification name")
    issuer: Optional[str] = Field(None, description="Issuing organization")
    year: Optional[str] = Field(None, description="Year obtained")


class CVExtractedData(BaseModel):
    profile: Optional[ProfileData] = Field(
        None, description="Personal information extracted from CV"
    )
    experience: List[WorkExperience] = Field(
        default_factory=list, description="Work experience entries"
    )
    education: List[Education] = Field(
        default_factory=list, description="Education entries"
    )
    skills: List[str] = Field(default_factory=list, description="List of skills")
    languages: List[str] = Field(
        default_factory=list, description="List of languages with proficiency"
    )
    certifications: List[Certification] = Field(
        default_factory=list, description="Professional certifications"
    )


class CVExtractionResponse(BaseModel):
    success: bool = True
    message: str = "CV extracted successfully"
    data: CVExtractedData
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
