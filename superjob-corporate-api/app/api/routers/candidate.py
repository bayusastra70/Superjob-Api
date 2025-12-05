from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from fastapi.security import HTTPBearer

from app.schemas.candidate import (
    CandidateScoreCreate, 
    CandidateScoreResponse, 
    CandidateRankingResponse
)
from app.services.candidate_service import CandidateService
from app.services.scoring_engine import ScoringEngine
from app.core.security import get_current_user
from app.schemas.models import OdooUser

router = APIRouter()
security = HTTPBearer()

# Tambahkan dependency di semua endpoints
@router.get("/jobs/{job_id}/candidates/ranking", response_model=List[CandidateRankingResponse])
async def get_candidate_ranking(
    job_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: OdooUser = Depends(get_current_user)  # ← TAMBAH INI
):
    """
    Get candidate ranking for a job
    """
    candidate_service = CandidateService()
    
    # Check if any candidate has scores
    if not candidate_service.candidate_has_score(job_id):
        return []
    
    ranking = candidate_service.get_candidate_ranking(job_id, limit, offset, sort_order)
    
    # Transform to response model
    response = []
    for candidate in ranking:
        response.append(CandidateRankingResponse(
            candidate_name=candidate['candidate_name'],
            application_id=candidate['application_id'],
            fit_score=float(candidate['fit_score']),
            skill_score=float(candidate['skill_score']) if candidate['skill_score'] else None,
            experience_score=float(candidate['experience_score']) if candidate['experience_score'] else None,
            education_score=float(candidate['education_score']) if candidate['education_score'] else None,
            reasons=candidate['reasons'],
            email=candidate.get('email'),
            phone=candidate.get('phone')
        ))
    
    return response

@router.post("/applications/{application_id}/calculate-score")
async def calculate_candidate_score(
    application_id: int,
    job_id: int = Query(..., description="Job ID for this application"),
    candidate_name: str = Query("Test Candidate", description="Candidate name"),
    current_user: OdooUser = Depends(get_current_user)  # ← TAMBAH INI
):
    """
    Trigger score calculation for a candidate application
    """
    try:
        scoring_engine = ScoringEngine()
        scoring_engine.trigger_scoring(application_id, job_id, candidate_name)
        
        return {
            "message": "Score calculation triggered successfully",
            "application_id": application_id,
            "job_id": job_id,
            "candidate_name": candidate_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating score: {str(e)}")

@router.get("/applications/{application_id}/score")
async def get_candidate_score(
    application_id: int,
    current_user: OdooUser = Depends(get_current_user)  # ← TAMBAH INI
):
    """
    Get score for a specific candidate application
    """
    candidate_service = CandidateService()
    score = candidate_service.get_candidate_score(application_id)
    
    if not score:
        raise HTTPException(status_code=404, detail="Score not found for this application")
    
    return score

@router.post("/init-candidate-scoring")
async def initialize_candidate_scoring(
    current_user: OdooUser = Depends(get_current_user)  # ← TAMBAH INI
):
    """
    Initialize candidate scoring system (create table, etc.)
    """
    try:
        candidate_service = CandidateService()
        candidate_service.create_candidate_score_table()
        
        return {
            "message": "Candidate scoring system initialized successfully",
            "status": "ready"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")