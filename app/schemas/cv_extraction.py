from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


VALID_INDONESIAN_MONTHS = {
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
}


class ProfileData(BaseModel):
    full_name: Optional[str] = Field(None, description="Full name of the candidate")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="City or country location")
    summary: Optional[str] = Field(None, description="Professional summary or bio")


class WorkExperience(BaseModel):
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Job position or title")
    start_month: Optional[str] = Field(
        None, description="Start month (Indonesian: Januari, Februari, etc.)"
    )
    start_year: Optional[str] = Field(None, description="Start year (4 digits)")
    end_month: Optional[str] = Field(
        None, description="End month (Indonesian: Januari, Februari, etc.)"
    )
    end_year: Optional[str] = Field(None, description="End year (4 digits)")
    is_current: Optional[bool] = Field(
        False, description="Whether this is current position"
    )
    description: Optional[str] = Field(
        None, description="Job responsibilities and achievements"
    )

    @field_validator("start_month", "end_month", mode="before")
    @classmethod
    def validate_month(cls, v):
        if v is not None and v not in VALID_INDONESIAN_MONTHS:
            raise ValueError(
                f"Invalid month '{v}'. Must be one of: {', '.join(sorted(VALID_INDONESIAN_MONTHS))}"
            )
        return v

    @field_validator("start_year", "end_year", mode="before")
    @classmethod
    def validate_year(cls, v):
        if v is not None and (not v.isdigit() or len(v) != 4):
            raise ValueError("Year must be exactly 4 digits")
        return v


class Education(BaseModel):
    institution: str = Field(..., description="School or university name")
    degree: str = Field(..., description="Degree (e.g., Sarjana, Magister, Doktor)")
    field: Optional[str] = Field(
        None, description="Field of study (e.g., Computer Science)"
    )
    start_month: Optional[str] = Field(
        None, description="Start month (Indonesian: Januari, Februari, etc.)"
    )
    start_year: Optional[str] = Field(None, description="Start year (4 digits)")
    end_month: Optional[str] = Field(
        None, description="End month (Indonesian: Januari, Februari, etc.)"
    )
    end_year: Optional[str] = Field(None, description="End year (4 digits)")
    is_current: Optional[bool] = Field(
        False, description="Whether currently studying here"
    )
    description: Optional[str] = Field(
        None, description="Additional description or achievements"
    )

    @field_validator("start_month", "end_month", mode="before")
    @classmethod
    def validate_month(cls, v):
        if v is not None and v not in VALID_INDONESIAN_MONTHS:
            raise ValueError(
                f"Invalid month '{v}'. Must be one of: {', '.join(sorted(VALID_INDONESIAN_MONTHS))}"
            )
        return v

    @field_validator("start_year", "end_year", mode="before")
    @classmethod
    def validate_year(cls, v):
        if v is not None and (not v.isdigit() or len(v) != 4):
            raise ValueError("Year must be exactly 4 digits")
        return v


class Certification(BaseModel):
    name: str = Field(..., description="Certification name")
    issuer: Optional[str] = Field(None, description="Issuing organization")
    issue_month: Optional[str] = Field(
        None, description="Issue month (Indonesian: Januari, Februari, etc.)"
    )
    issue_year: Optional[str] = Field(None, description="Issue year (4 digits)")

    @field_validator("issue_month", mode="before")
    @classmethod
    def validate_month(cls, v):
        if v is not None and v not in VALID_INDONESIAN_MONTHS:
            raise ValueError(
                f"Invalid month '{v}'. Must be one of: {', '.join(sorted(VALID_INDONESIAN_MONTHS))}"
            )
        return v

    @field_validator("issue_year", mode="before")
    @classmethod
    def validate_year(cls, v):
        if v is not None and (not v.isdigit() or len(v) != 4):
            raise ValueError("Year must be exactly 4 digits")
        return v


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
