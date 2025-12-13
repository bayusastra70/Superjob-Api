from dataclasses import dataclass
from typing import Dict, Optional, Sequence

from app.models.job_posting import JobPosting, JobStatus


@dataclass
class ScoreResult:
    score: Optional[float]
    grade: Optional[str]
    details: Dict[str, float]


WEIGHTS = {
    "title": 10,
    "description": 20,
    "salary": 15,
    "skills": 15,
    "location": 8,
    "employment_type": 6,
    "experience_level": 6,
    "education": 5,
    "benefits": 6,
    "contact": 5,
}


def _text_score(text: Optional[str], weight: float) -> float:
    if not text:
        return 0.0
    length = len(text.strip())
    if length >= 150:
        return weight
    if length >= 80:
        return weight * 0.5
    return 0.0


def _skills_score(skills: Sequence[str], weight: float) -> float:
    count = len([s for s in skills if s])
    if count >= 3:
        return weight
    if 1 <= count <= 2:
        return weight * 0.5
    return 0.0


def compute_quality_score(job: JobPosting) -> ScoreResult:
    """
    Compute job quality score based on rule v1.
    Returns ScoreResult(score=None, grade=None, details={}) for draft jobs.
    """
    if job.status == JobStatus.draft:
        return ScoreResult(score=None, grade=None, details={})

    details: Dict[str, float] = {}

    details["title"] = WEIGHTS["title"] if job.title else 0.0
    details["description"] = _text_score(job.description, WEIGHTS["description"])
    details["salary"] = WEIGHTS["salary"] if job.salary_min is not None or job.salary_max is not None else 0.0
    details["skills"] = _skills_score(job.skills or [], WEIGHTS["skills"])
    details["location"] = WEIGHTS["location"] if job.location else 0.0
    details["employment_type"] = WEIGHTS["employment_type"] if job.employment_type else 0.0
    details["experience_level"] = WEIGHTS["experience_level"] if job.experience_level else 0.0
    details["education"] = WEIGHTS["education"] if job.education else 0.0
    details["benefits"] = WEIGHTS["benefits"] if job.benefits else 0.0
    details["contact"] = WEIGHTS["contact"] if job.contact_url else 0.0

    total = round(sum(details.values()), 2)

    if total >= 85:
        grade = "Excellent"
    elif total >= 60:
        grade = "Good"
    else:
        grade = "Low"

    return ScoreResult(score=total, grade=grade, details=details)
