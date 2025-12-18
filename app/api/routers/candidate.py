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
    "/jobs/{job_id}/candidates/ranking",
    response_model=List[CandidateRankingResponse],
    summary="Get Candidate Ranking",
    description="""
    Mendapatkan ranking kandidat untuk lowongan tertentu.
    
    **Tujuan:**
    Endpoint ini mengembalikan daftar kandidat yang sudah di-score,
    diurutkan berdasarkan fit_score (skor kesesuaian dengan lowongan).
    
    **Format job_id:** Integer (contoh: `1`)
    
    **Query Parameters:**
    - `limit`: Jumlah maksimal kandidat (default: 50, max: 100)
    - `offset`: Offset untuk pagination (default: 0)
    - `sort_order`: Urutan sorting - `asc` atau `desc` (default: desc)
    
    **Data yang Dikembalikan per Kandidat:**
    - `candidate_name`: Nama kandidat
    - `application_id`: ID lamaran
    - `fit_score`: Skor kesesuaian (0-100)
    - `skill_score`: Skor kemampuan teknis
    - `experience_score`: Skor pengalaman
    - `education_score`: Skor pendidikan
    - `reasons`: Alasan/catatan penilaian
    - `email`, `phone`: Kontak kandidat
    
    **Catatan:**
    - Mengembalikan array kosong jika belum ada kandidat yang di-score.
    - Skor dihitung menggunakan AI scoring engine.
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Ranking kandidat berhasil diambil"},
    },
)
async def get_candidate_ranking(
    job_id: int = Path(
        ...,
        description="Job ID untuk mengambil ranking kandidat",
        example=1,
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Jumlah maksimal kandidat yang dikembalikan",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Offset untuk pagination",
    ),
    sort_order: str = Query(
        "desc",
        regex="^(asc|desc)$",
        description="Urutan sorting: asc (terendah dulu) atau desc (tertinggi dulu)",
    ),
    current_user: OdooUser = Depends(get_current_user),
):
    """
    Mendapatkan ranking kandidat untuk lowongan tertentu.

    Args:
        job_id: ID lowongan untuk mengambil ranking.
        limit: Jumlah maksimal kandidat.
        offset: Offset untuk pagination.
        sort_order: Urutan sorting (asc/desc).
        current_user: User yang sedang login.

    Returns:
        List[CandidateRankingResponse]: Daftar kandidat dengan skor.
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


@router.post(
    "/applications/{application_id}/calculate-score",
    summary="Calculate Candidate Score",
    description="""
    Menjalankan perhitungan skor untuk kandidat tertentu.
    
    **Tujuan:**
    Endpoint ini men-trigger proses scoring menggunakan AI engine
    untuk menghitung kesesuaian kandidat dengan lowongan.
    
    **Format application_id:** Integer (contoh: `1`)
    
    **Query Parameters:**
    - `job_id` (required): ID lowongan untuk konteks scoring
    - `candidate_name` (optional): Nama kandidat (default: "Test Candidate")
    
    **Proses Scoring:**
    1. Mengambil data kandidat dari application
    2. Mengambil requirements dari job posting
    3. AI menghitung fit_score, skill_score, experience_score
    4. Hasil disimpan ke database
    
    **Response:**
    - `200 OK`: Scoring berhasil di-trigger
    - `500 Internal Server Error`: Gagal menghitung skor
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Proses scoring bisa memakan waktu beberapa detik.
    - Skor bisa diambil menggunakan endpoint GET /applications/{id}/score
    """,
    responses={
        200: {"description": "Score calculation berhasil di-trigger"},
        500: {"description": "Gagal menghitung skor"},
    },
)
async def calculate_candidate_score(
    application_id: int = Path(
        ...,
        description="Application ID untuk dihitung skornya",
        example=1,
    ),
    job_id: int = Query(
        ...,
        description="Job ID untuk konteks scoring",
        example=1,
    ),
    candidate_name: str = Query(
        "Test Candidate",
        description="Nama kandidat",
    ),
    current_user: OdooUser = Depends(get_current_user),
):
    """
    Menjalankan perhitungan skor untuk kandidat.

    Args:
        application_id: ID lamaran yang akan di-score.
        job_id: ID lowongan untuk konteks scoring.
        candidate_name: Nama kandidat.
        current_user: User yang sedang login.

    Returns:
        dict: Message sukses dengan detail trigger.

    Raises:
        HTTPException: 500 jika gagal menghitung skor.
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


@router.get(
    "/applications/{application_id}/score",
    summary="Get Candidate Score",
    description="""
    Mendapatkan skor kandidat untuk lamaran tertentu.
    
    **Format application_id:** Integer (contoh: `1`)
    
    **Data yang Dikembalikan:**
    - `application_id`: ID lamaran
    - `fit_score`: Skor kesesuaian total (0-100)
    - `skill_score`: Skor kemampuan teknis
    - `experience_score`: Skor pengalaman kerja
    - `education_score`: Skor pendidikan
    - `reasons`: Alasan/catatan dari AI scoring
    - `scored_at`: Waktu skor dihitung
    
    **Response:**
    - `200 OK`: Skor berhasil diambil
    - `404 Not Found`: Skor belum dihitung untuk lamaran ini
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Jika skor belum ada, gunakan POST /applications/{id}/calculate-score terlebih dahulu.
    """,
    responses={
        200: {"description": "Skor kandidat berhasil diambil"},
        404: {"description": "Skor tidak ditemukan untuk lamaran ini"},
    },
)
async def get_candidate_score(
    application_id: int = Path(
        ...,
        description="Application ID untuk mengambil skor",
        example=1,
    ),
    current_user: OdooUser = Depends(get_current_user),
):
    """
    Mendapatkan skor kandidat untuk lamaran tertentu.

    Args:
        application_id: ID lamaran yang ingin diambil skornya.
        current_user: User yang sedang login.

    Returns:
        dict: Skor kandidat dengan breakdown per kategori.

    Raises:
        HTTPException: 404 jika skor tidak ditemukan.
    """
    candidate_service = CandidateService()
    score = candidate_service.get_candidate_score(application_id)

    if not score:
        raise HTTPException(
            status_code=404, detail="Score not found for this application"
        )

    return score


@router.post(
    "/init-candidate-scoring",
    summary="Initialize Candidate Scoring System",
    description="""
    Inisialisasi sistem scoring kandidat.
    
    **Tujuan:**
    Endpoint ini membuat tabel dan struktur database yang diperlukan
    untuk sistem scoring kandidat.
    
    **Operasi yang Dilakukan:**
    - Membuat tabel `candidate_scores` jika belum ada
    - Membuat index yang diperlukan
    - Mempersiapkan struktur untuk menyimpan skor
    
    **Response:**
    - `200 OK`: Inisialisasi berhasil
    - `500 Internal Server Error`: Inisialisasi gagal
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Endpoint ini hanya perlu dipanggil sekali saat setup awal.
    - Aman untuk dipanggil berulang kali (idempotent).
    """,
    responses={
        200: {"description": "Sistem scoring berhasil diinisialisasi"},
        500: {"description": "Inisialisasi gagal"},
    },
)
async def initialize_candidate_scoring(
    current_user: OdooUser = Depends(get_current_user),
):
    """
    Inisialisasi sistem scoring kandidat.

    Args:
        current_user: User yang sedang login.

    Returns:
        dict: Status inisialisasi.

    Raises:
        HTTPException: 500 jika inisialisasi gagal.
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
    
    **Response:**
    - `200 OK`: Upload selesai (cek detail successful/failed)
    - `400 Bad Request`: File bukan CSV atau encoding error
    - `500 Internal Server Error`: Error memproses file
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Activity log akan dicatat untuk setiap upload.
    - Maksimal 10 error yang ditampilkan di response.
    """,
    responses={
        200: {"description": "Upload selesai (cek detail di response)"},
        400: {"description": "File tidak valid atau encoding error"},
        500: {"description": "Error memproses file"},
    },
)
async def bulk_upload_candidates(
    request: Request,
    job_id: int = Path(
        ...,
        description="Job ID untuk kandidat",
        example=1,
    ),
    file: UploadFile = File(
        ...,
        description="File CSV berisi data kandidat",
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Bulk upload kandidat dari file CSV.

    Args:
        request: Request object untuk logging.
        job_id: ID lowongan untuk kandidat.
        file: File CSV yang diupload.
        current_user: User yang sedang login.

    Returns:
        dict: Hasil upload dengan detail sukses/gagal.

    Raises:
        HTTPException: 400 jika file tidak valid.
        HTTPException: 500 jika error memproses file.
    """

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
