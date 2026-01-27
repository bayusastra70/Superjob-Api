from typing import List, Optional
from pydantic import BaseModel, HttpUrl


# --- Profile Schema ---
class ProfileResponse(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


# --- Team Members Schema ---
class TeamMemberResponse(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    role: Optional[str] = None
    profile_picture: Optional[str] = None


# --- Company Profile Schema ---
class CompanyProfileResponse(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None


# --- Jobs Trend Schema ---
class JobsTrendItemResponse(BaseModel):
    month: Optional[str] = None
    total_jobs: Optional[int] = None


class JobsTrendResponse(BaseModel):
    year: Optional[int] = None
    unit: Optional[str] = None
    data: Optional[List[JobsTrendItemResponse]] = None


# --- Most Applied Jobs Schema ---
class MostAppliedJobResponse(BaseModel):
    job_id: Optional[int] = None
    title: Optional[str] = None
    total_applicants: Optional[int] = None
    max_applicants: Optional[int] = None


# --- Jobs Summary Schema ---
class JobsSummaryResponse(BaseModel):
    active_jobs: Optional[int] = None
    total_applications: Optional[int] = None
    new_applications: Optional[int] = None
    new_jobs: Optional[int] = None
    most_applied_jobs: Optional[List[MostAppliedJobResponse]] = None
    jobs_trend: Optional[JobsTrendResponse] = None


# --- Main Dashboard Response Schema ---
class DashboardDataResponse(BaseModel):
    profile: Optional[ProfileResponse] = None
    team_members: Optional[List[TeamMemberResponse]] = None
    company_profile: Optional[CompanyProfileResponse] = None
    jobs_summary: Optional[JobsSummaryResponse] = None