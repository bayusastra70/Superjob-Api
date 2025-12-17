from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Depends,
    UploadFile,
    File,
    Request,
    Path,
)
from typing import List, Optional
from fastapi.security import HTTPBearer
import csv
import io
import logging


from app.schemas.candidate import (
    CandidateScoreCreate,
    CandidateScoreResponse,
    CandidateRankingResponse,
)
from app.services.candidate_service import CandidateService
from app.services.scoring_engine import ScoringEngine
from app.core.security import get_current_user
from app.schemas.models import OdooUser
from app.schemas.user import UserResponse
from app.services.activity_log_service import activity_log_service

router = APIRouter(tags=["candidate"])
security = HTTPBearer()
logger = logging.getLogger(__name__)


# Tambahkan dependency di semua endpoints
@router.get(
    "/jobs/{job_id}/candidates/ranking", response_model=List[CandidateRankingResponse]
)
async def get_candidate_ranking(
    job_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: OdooUser = Depends(get_current_user),  # ← TAMBAH INI
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
        response.append(
            CandidateRankingResponse(
                candidate_name=candidate["candidate_name"],
                application_id=candidate["application_id"],
                fit_score=float(candidate["fit_score"]),
                skill_score=float(candidate["skill_score"])
                if candidate["skill_score"]
                else None,
                experience_score=float(candidate["experience_score"])
                if candidate["experience_score"]
                else None,
                education_score=float(candidate["education_score"])
                if candidate["education_score"]
                else None,
                reasons=candidate["reasons"],
                email=candidate.get("email"),
                phone=candidate.get("phone"),
            )
        )

    return response


@router.post("/applications/{application_id}/calculate-score")
async def calculate_candidate_score(
    application_id: int,
    job_id: int = Query(..., description="Job ID for this application"),
    candidate_name: str = Query("Test Candidate", description="Candidate name"),
    current_user: OdooUser = Depends(get_current_user),  # ← TAMBAH INI
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
            "candidate_name": candidate_name,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating score: {str(e)}"
        )


@router.get("/applications/{application_id}/score")
async def get_candidate_score(
    application_id: int,
    current_user: OdooUser = Depends(get_current_user),  # ← TAMBAH INI
):
    """
    Get score for a specific candidate application
    """
    candidate_service = CandidateService()
    score = candidate_service.get_candidate_score(application_id)

    if not score:
        raise HTTPException(
            status_code=404, detail="Score not found for this application"
        )

    return score


@router.post("/init-candidate-scoring")
async def initialize_candidate_scoring(
    current_user: OdooUser = Depends(get_current_user),  # ← TAMBAH INI
):
    """
    Initialize candidate scoring system (create table, etc.)
    """
    try:
        candidate_service = CandidateService()
        candidate_service.create_candidate_score_table()

        return {
            "message": "Candidate scoring system initialized successfully",
            "status": "ready",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")


@router.post(
    "/jobs/{job_id}/candidates/upload",
    summary="Bulk Upload Candidates",
    description="""
    Upload kandidat secara bulk menggunakan file CSV.
    
    **Format CSV:**
    - Header: `name,email,phone,experience_years,skills,education`
    - Delimiter: comma (,)
    - Encoding: UTF-8
    
    **Contoh CSV:**
    ```
    name,email,phone,experience_years,skills,education
    John Doe,john@example.com,+62812345678,5,"Python,JavaScript",S1 Informatika
    Jane Smith,jane@example.com,+62898765432,3,"Java,Spring",S1 Sistem Informasi
    ```
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
async def bulk_upload_candidates(
    request: Request,
    job_id: int = Path(..., description="Job ID untuk kandidat"),
    file: UploadFile = File(..., description="File CSV berisi data kandidat"),
    current_user: UserResponse = Depends(get_current_user),
):
    """Bulk upload candidates from CSV file"""

    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File harus berformat CSV")

    try:
        # Read file content
        content = await file.read()
        decoded_content = content.decode("utf-8")

        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(decoded_content))

        candidate_service = CandidateService()

        total_candidates = 0
        successful = 0
        failed = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            total_candidates += 1

            try:
                name = row.get("name", "").strip()
                email = row.get("email", "").strip()

                if not name:
                    raise ValueError("Name is required")
                if not email:
                    raise ValueError("Email is required")

                phone = row.get("phone", "").strip() or None
                experience_years = row.get("experience_years", "").strip()
                skills = row.get("skills", "").strip() or None
                education = row.get("education", "").strip() or None

                exp_years = None
                if experience_years:
                    try:
                        exp_years = int(experience_years)
                    except ValueError:
                        exp_years = None

                result = candidate_service.create_candidate_for_job(
                    job_id=job_id,
                    name=name,
                    email=email,
                    phone=phone,
                    experience_years=exp_years,
                    skills=skills.split(",") if skills else None,
                    education=education,
                )

                if result:
                    successful += 1
                else:
                    failed += 1
                    errors.append(f"Row {row_num}: Failed to create candidate")

            except Exception as e:
                failed += 1
                errors.append(f"Row {row_num}: Failed to create candidate")
                logger.warning(f"Failed to process row {row_num}: {e}")

        # Log activity
        activity_log_service.log_candidate_uploaded(
            employer_id=current_user.id,
            job_id=job_id,
            total_candidate=total_candidates,
            successful=successful,
            failed=failed,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            role="employer",
        )

        return {
            "message": f"Upload completed: {successful}/{total_candidates} candidates processed",
            "job_id": job_id,
            "total": total_candidates,
            "successful": successful,
            "failed": failed,
            "errors": errors[:10] if errors else [],  # Returns first 10 errors only
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File encoding error. Pastikan file ber-encoding UTF-8",
        )
    except Exception as e:
        logger.error(f"Error processing CSV upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
