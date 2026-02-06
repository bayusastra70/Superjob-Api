
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class ScoreCategory(str, Enum):
    BASIC_INFO = "basic_info"
    JOB_DETAILS = "job_details"
    REQUIREMENTS = "requirements"
    SALARY = "salary"
    CONTACT = "contact"
    AI_INTERVIEW = "ai_interview"


class JobScoreItem(BaseModel):
    """Item untuk scoring criteria"""
    category: str = Field(..., description="Kategori penilaian")
    criteria: str = Field(..., description="Kriteria penilaian")
    field_name: str = Field(..., description="Nama field di database")
    weight: float = Field(..., description="Bobot kriteria (0-1)")
    score: float = Field(..., ge=0, le=100, description="Nilai (0-100)")
    is_met: bool = Field(..., description="Apakah kriteria terpenuhi")
    suggestion: Optional[str] = Field(None, description="Saran perbaikan")
    max_score: int = Field(default=100, description="Nilai maksimal")

class RecommendationItem(BaseModel):
    title: str
    description: str

class JobScoreResponse(BaseModel):
    """Response untuk job scoring"""
    job_id: int
    job_title: str
    job_code: Optional[str]
    score: float = Field(..., ge=0, le=120, description="Skor keseluruhan (0-120)")
    grade: str = Field(..., description="Label kualitas (Poor, Fair, Good, Excellent)")
    meta: Dict = Field(default_factory=dict, description="Metadata tambahan")

    completion_rate: float = Field(..., ge=0, le=100, description="Persentase kelengkapan")
    category_scores: Dict[str, float] = Field(..., description="Skor per kategori")
    category_weights: Optional[Dict[str, float]] = None
    criteria_details: Optional[List[JobScoreItem]] = None
    recommendations: Optional[List[RecommendationItem]] = None
    missing_fields: List[str] = Field(..., description="Field yang belum diisi")
    scored_at: datetime = Field(default_factory=datetime.now)


    


class JobScoringOverview(BaseModel):
    """Overview scoring untuk employer"""
    employer_id: int
    average_score: float
    total_jobs: int
    quality_distribution: Dict[str, int]
    category_averages: Dict[str, float]
    top_performers: List[Dict]
    needs_improvement: List[Dict]
    completion_stats: Dict[str, float]
    scored_jobs_count: int