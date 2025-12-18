from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from loguru import logger
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.job_posting import JobPosting, JobStatus
from app.schemas.job_post import JobPostingOut, JobPostingList, JobPostingCreate
from app.schemas.applicant import ApplicantOut, ApplicantList
from app.schemas.message import MessageOut, MessageList
from app.schemas.company import CompanyProfileOut

router = APIRouter(prefix="/employers/{employer_id}", tags=["employer-resources"])


@router.get(
    "/jobs",
    response_model=JobPostingList,
    summary="List Job Postings",
    description="""
    Mendapatkan daftar semua lowongan kerja milik employer.
    
    **Format employer_id:** Integer
    
    **Test Data yang tersedia:**
    - employer_id `8` (employer@superjob.com) - 4 job postings
    - employer_id `3` (tanaka@gmail.com) - 2 job postings
    """,
)
async def list_jobs(
    employer_id: int = Path(
        ...,
        description="ID Employer. Gunakan 8 atau 3 untuk testing.",
        example=8,
    ),
    limit: int = Query(20, ge=1, le=100, description="Jumlah item per halaman"),
    offset: int = Query(0, ge=0, description="Offset untuk pagination"),
    db: AsyncSession = Depends(get_db),
) -> JobPostingList:
    total = await db.scalar(
        select(func.count())
        .select_from(JobPosting)
        .where(JobPosting.employer_id == employer_id)
    )
    stmt = (
        select(JobPosting)
        .where(JobPosting.employer_id == employer_id)
        .order_by(JobPosting.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return JobPostingList(items=rows, total=total or 0)


@router.post(
    "/jobs",
    response_model=JobPostingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Job Posting",
    description="""
    Membuat lowongan kerja baru.
    
    **Status yang valid:** draft, published, closed, archived
    """,
)
async def create_job(
    employer_id: int = Path(..., description="ID Employer", example=8),
    payload: JobPostingCreate = ...,
    db: AsyncSession = Depends(get_db),
) -> JobPostingOut:
    allowed_status = {s.value for s in JobStatus}
    status_value = (
        payload.status if payload.status in allowed_status else JobStatus.draft.value
    )

    job = JobPosting(
        employer_id=employer_id,
        title=payload.title,
        description=payload.description,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        salary_currency=payload.salary_currency,
        skills=payload.skills,
        location=payload.location,
        employment_type=payload.employment_type,
        experience_level=payload.experience_level,
        education=payload.education,
        benefits=payload.benefits,
        contact_url=payload.contact_url,
        status=status_value,
    )
    db.add(job)
    try:
        await db.commit()
        await db.refresh(job)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to create job", exc=exc, employer_id=str(employer_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job",
        )
    return job


@router.get(
    "/jobs/{job_id}",
    response_model=JobPostingOut,
    summary="Get Job Detail",
    description="""
    Mendapatkan detail lowongan kerja berdasarkan ID.
    
    **Format job_id:** String UUID (contoh: `11111111-1111-1111-1111-111111111111`)
    
    **Test Data:**
    - `11111111-1111-1111-1111-111111111111` (Senior Software Engineer)
    - `11111111-1111-1111-1111-111111111112` (Junior Frontend Developer)
    """,
)
async def get_job_detail(
    employer_id: int = Path(..., description="ID Employer", example=8),
    job_id: str = Path(
        ...,
        description="Job ID (UUID format)",
        example="11111111-1111-1111-1111-111111111111",
    ),
    db: AsyncSession = Depends(get_db),
) -> JobPostingOut:
    job = await db.get(JobPosting, job_id)
    if job is None or job.employer_id != employer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return job


async def _safe_list(db: AsyncSession, query: str, params: dict) -> list[dict]:
    try:
        result = await db.execute(text(query), params)
        rows = result.mappings().all()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.warning("List query failed, returning empty", exc=exc, query=query)
        return []


@router.get(
    "/applicants",
    response_model=ApplicantList,
    summary="List Applicants",
    description="""
    Mendapatkan daftar semua pelamar (applicants) untuk employer tertentu.
    
    **Tujuan:**
    Endpoint ini mengembalikan daftar kandidat yang telah melamar 
    ke lowongan kerja milik employer yang ditentukan.
    
    **Data yang Dikembalikan:**
    - `id`: ID unik pelamar
    - `employer_id`: ID employer terkait
    - `job_id`: ID lowongan yang dilamar
    - `name`: Nama pelamar
    - `email`: Email pelamar
    - `status`: Status lamaran (applied, reviewed, interviewed, offered, rejected)
    - `created_at`: Waktu lamaran dibuat
    
    **Pagination:**
    - Gunakan `limit` dan `offset` untuk pagination.
    - Default: 20 items per halaman.
    
    **Catatan:**
    - Jika tabel `applicants` belum ada, akan mengembalikan list kosong.
    """,
    responses={
        200: {"description": "Daftar pelamar berhasil diambil"},
    },
)
async def list_applicants(
    employer_id: int = Path(
        ...,
        description="ID Employer untuk filter pelamar",
        example=8,
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Jumlah maksimal item per halaman (1-100)",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Jumlah item yang di-skip untuk pagination",
    ),
    db: AsyncSession = Depends(get_db),
) -> ApplicantList:
    """
    Mengambil daftar pelamar untuk employer tertentu.

    Args:
        employer_id: ID employer untuk filter data.
        limit: Jumlah maksimal item yang dikembalikan.
        offset: Offset untuk pagination.
        db: Database session.

    Returns:
        ApplicantList: Daftar pelamar dengan total count.
    """
    rows = await _safe_list(
        db,
        """
        SELECT id, employer_id, job_id, name, email, status, created_at
        FROM applicants
        WHERE employer_id = :employer_id
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
        """,
        {"employer_id": employer_id, "limit": limit, "offset": offset},
    )
    total_rows = await _safe_list(
        db,
        "SELECT COUNT(*) AS c FROM applicants WHERE employer_id = :employer_id",
        {"employer_id": employer_id},
    )
    total = total_rows[0]["c"] if total_rows else 0
    return ApplicantList(items=[ApplicantOut(**r) for r in rows], total=total)


@router.get(
    "/messages",
    response_model=MessageList,
    summary="List Messages",
    description="""
    Mendapatkan daftar pesan (messages) untuk employer tertentu.
    
    **Tujuan:**
    Endpoint ini mengembalikan daftar pesan inbox untuk employer,
    termasuk pesan dari kandidat, sistem notifikasi, dll.
    
    **Data yang Dikembalikan:**
    - `id`: ID unik pesan
    - `employer_id`: ID employer penerima
    - `sender`: Nama pengirim pesan
    - `subject`: Subjek pesan
    - `preview`: Preview singkat isi pesan
    - `created_at`: Waktu pesan diterima
    - `is_read`: Status baca pesan (true/false)
    
    **Filter:**
    - `unread_only=true`: Hanya tampilkan pesan yang belum dibaca.
    - `unread_only=false` (default): Tampilkan semua pesan.
    
    **Pagination:**
    - Gunakan `limit` dan `offset` untuk pagination.
    - Default: 20 items per halaman.
    
    **Catatan:**
    - Jika tabel `messages` belum ada, akan mengembalikan list kosong.
    """,
    responses={
        200: {"description": "Daftar pesan berhasil diambil"},
    },
)
async def list_messages(
    employer_id: int = Path(
        ...,
        description="ID Employer untuk filter pesan",
        example=8,
    ),
    unread_only: bool = Query(
        False,
        description="Filter hanya pesan yang belum dibaca",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Jumlah maksimal item per halaman (1-100)",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Jumlah item yang di-skip untuk pagination",
    ),
    db: AsyncSession = Depends(get_db),
) -> MessageList:
    """
    Mengambil daftar pesan untuk employer tertentu.

    Args:
        employer_id: ID employer untuk filter data.
        unread_only: Jika True, hanya tampilkan pesan belum dibaca.
        limit: Jumlah maksimal item yang dikembalikan.
        offset: Offset untuk pagination.
        db: Database session.

    Returns:
        MessageList: Daftar pesan dengan total count.
    """
    filter_clause = "AND is_read = false" if unread_only else ""
    rows = await _safe_list(
        db,
        f"""
        SELECT id, employer_id, sender, subject, preview, created_at, is_read
        FROM messages
        WHERE employer_id = :employer_id
        {filter_clause}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
        """,
        {"employer_id": employer_id, "limit": limit, "offset": offset},
    )
    total_rows = await _safe_list(
        db,
        f"SELECT COUNT(*) AS c FROM messages WHERE employer_id = :employer_id {filter_clause}",
        {"employer_id": employer_id},
    )
    total = total_rows[0]["c"] if total_rows else 0
    return MessageList(items=[MessageOut(**r) for r in rows], total=total)


@router.get(
    "/company-profile",
    response_model=CompanyProfileOut,
    summary="Get Company Profile",
    description="""
    Mendapatkan profil perusahaan untuk employer tertentu.
    
    **Tujuan:**
    Endpoint ini mengembalikan informasi profil perusahaan yang
    terkait dengan employer, digunakan untuk menampilkan informasi
    perusahaan di halaman lowongan kerja.
    
    **Data yang Dikembalikan:**
    - `employer_id`: ID employer terkait
    - `name`: Nama perusahaan
    - `website`: URL website perusahaan
    - `description`: Deskripsi singkat perusahaan
    - `address`: Alamat kantor
    - `phone`: Nomor telepon
    - `email`: Email kontak perusahaan
    
    **Catatan:**
    - Jika profil perusahaan belum ada, akan mengembalikan objek minimal
      dengan hanya `employer_id` yang terisi.
    - Endpoint ini graceful dan tidak akan error meskipun data tidak ada.
    """,
    responses={
        200: {"description": "Profil perusahaan berhasil diambil"},
    },
)
async def get_company_profile(
    employer_id: int = Path(
        ...,
        description="ID Employer untuk mengambil profil perusahaan",
        example=8,
    ),
    db: AsyncSession = Depends(get_db),
) -> CompanyProfileOut:
    """
    Mengambil profil perusahaan untuk employer tertentu.

    Args:
        employer_id: ID employer untuk filter data.
        db: Database session.

    Returns:
        CompanyProfileOut: Profil perusahaan atau objek minimal jika tidak ditemukan.
    """
    rows = await _safe_list(
        db,
        """
        SELECT employer_id, name, website, description, address, phone, email
        FROM company_profiles
        WHERE employer_id = :employer_id
        LIMIT 1
        """,
        {"employer_id": employer_id},
    )
    if not rows:
        # Graceful fallback with minimal data
        return CompanyProfileOut(employer_id=employer_id)
    return CompanyProfileOut(**rows[0])
