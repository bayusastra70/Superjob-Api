from fastapi import APIRouter, HTTPException, Depends, Path, Body
import logging

from app.schemas.interview_feedback_schema import (
    InterviewFeedbackCreate,
    InterviewFeedbackUpdate,
    InterviewFeedbackResponse,
    InterviewFeedbackOptionalResponse,
)
from app.services.interview_feedback_service import interview_feedback_service
from app.core.security import get_current_user
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interview-feedbacks", tags=["Interview Feedback"])


@router.post(
    "/",
    response_model=InterviewFeedbackResponse,
    summary="Submit Interview Feedback",
    description="""
    Menyimpan rating dan feedback interview untuk kandidat.
    
    **Validasi:**
    - `rating` wajib diisi (1-5)
    - [feedback](cci:1://file:///c:/MyProject/superjob-api/app/schemas/interview_feedback_schema.py:15:4-20:16) opsional, tapi jika diisi minimal 10 karakter, maksimal 500 karakter
    - Satu application hanya bisa memiliki satu feedback (unique constraint)
    
    **Error Codes:**
    - 400: Rating wajib diisi / Feedback minimal 10 karakter / Feedback maksimal 500 karakter
    - 404: Application tidak ditemukan
    - 409: Feedback sudah ada untuk application ini
    
    **Contoh Request:**
    ```json
    {
        "application_id": 1,
        "rating": 4,
        "feedback": "Kandidat memiliki skill teknis yang baik dan komunikatif"
    }
    ```
    
    **⚠️ Membutuhkan Authorization Token (Employer only)!**
    """,
    responses={
        200: {"description": "Feedback berhasil disimpan"},
        400: {"description": "Validasi error"},
        404: {"description": "Application tidak ditemukan"},
        409: {"description": "Feedback sudah ada"},
    },
)
async def submit_feedback(
    feedback_data: InterviewFeedbackCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Submit new interview feedback"""
    try:
        # Validation sudah dilakukan di Pydantic schema
        # Tapi kita tambahkan pesan error yang lebih user-friendly

        result = interview_feedback_service.create_feedback(
            feedback_data, created_by=current_user.id
        )

        if result is None:
            raise HTTPException(status_code=500, detail="Gagal menyimpan feedback")

        # Check for error response from service
        if "error" in result:
            raise HTTPException(
                status_code=result.get("code", 400), detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/application/{application_id}",
    response_model=InterviewFeedbackOptionalResponse,
    summary="Get Feedback by Application",
    description="""
    Mendapatkan feedback interview berdasarkan application ID.
    
    **Response Behavior:**
    - Jika feedback **ada**: Return 200 dengan data lengkap + `exists: true`
    - Jika feedback **belum ada**: Return 200 dengan empty structure + `exists: false`
    
    **Contoh Response (ada data):**
    ```json
    {
        "id": "uuid-here",
        "application_id": 1,
        "rating": 4,
        "feedback": "Kandidat bagus",
        "created_by": 5,
        "created_at": "2025-12-16T15:00:00",
        "updated_at": "2025-12-16T15:00:00",
        "exists": true
    }
    ```
    
    **Contoh Response (belum ada data):**
    ```json
    {
        "id": null,
        "application_id": 1,
        "rating": null,
        "feedback": null,
        "created_by": null,
        "created_at": null,
        "updated_at": null,
        "exists": false
    }
    ```
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Feedback data (atau empty structure jika belum ada)"},
    },
)
async def get_feedback_by_application(
    application_id: int = Path(..., description="Application ID", example=1),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get interview feedback by application ID - always returns 200"""
    try:
        feedback = interview_feedback_service.get_feedback_by_application(
            application_id
        )
        if not feedback:
            # Return empty structure instead of 404
            return InterviewFeedbackOptionalResponse.empty(
                application_id=application_id
            )
        # Return with exists=True
        return InterviewFeedbackOptionalResponse.from_dict(feedback)
    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{feedback_id}",
    response_model=InterviewFeedbackResponse,
    summary="Get Feedback by ID",
    description="""
    Mendapatkan feedback interview berdasarkan feedback ID (UUID).
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
async def get_feedback(
    feedback_id: str = Path(..., description="Feedback ID (UUID)"),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get interview feedback by ID"""
    try:
        feedback = interview_feedback_service.get_feedback_by_id(feedback_id)

        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback tidak ditemukan")

        return feedback

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{feedback_id}",
    response_model=InterviewFeedbackResponse,
    summary="Update Interview Feedback",
    description="""
    Memperbarui rating dan/atau feedback interview.
    
    **Validasi:**
    - `rating` opsional, tapi jika diisi harus 1-5
    - [feedback](cci:1://file:///c:/MyProject/superjob-api/app/schemas/interview_feedback_schema.py:15:4-20:16) opsional, tapi jika diisi minimal 10 karakter, maksimal 500 karakter
    
    **Contoh Request:**
    ```json
    {
        "rating": 5,
        "feedback": "Update: Kandidat sangat baik dalam technical interview"
    }
    ```
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
async def update_feedback(
    feedback_id: str = Path(..., description="Feedback ID (UUID)"),
    update_data: InterviewFeedbackUpdate = Body(...),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update interview feedback"""
    try:
        result = interview_feedback_service.update_feedback(
            feedback_id, update_data, updated_by=current_user.id
        )

        if result is None:
            raise HTTPException(status_code=500, detail="Gagal update feedback")

        # Check for error response from service
        if "error" in result:
            raise HTTPException(
                status_code=result.get("code", 400), detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/application/{application_id}",
    response_model=InterviewFeedbackResponse,
    summary="Update Feedback by Application ID",
    description="""
    Memperbarui rating dan/atau feedback interview berdasarkan Application ID.
    
    **Lebih praktis** daripada update by feedback UUID karena employer biasanya tau application ID.
    
    **Validasi:**
    - `rating` opsional, tapi jika diisi harus 1-5
    - [feedback](cci:1://file:///c:/MyProject/superjob-api/app/api/routers/interview_feedback.py:116:0-143:59) opsional, tapi jika diisi minimal 10 karakter, maksimal 500 karakter
    
    **Audit Trail:**
    - `updated_at` akan otomatis diupdate ke waktu sekarang
    
    **Contoh Request:**
    ```json
    {
        "rating": 5,
        "feedback": "Update setelah final interview: Kandidat sangat recommended"
    }
    ```
    
    **⚠️ Membutuhkan Authorization Token (Employer only)!**
    """,
    responses={
        200: {"description": "Feedback berhasil diupdate"},
        400: {"description": "Tidak ada data untuk diupdate"},
        404: {"description": "Feedback tidak ditemukan untuk application ini"},
    },
)
async def update_feedback_by_application(
    application_id: int = Path(..., description="Application ID", example=1),
    update_data: InterviewFeedbackUpdate = Body(...),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update interview feedback by application ID"""
    try:
        result = interview_feedback_service.update_feedback_by_application(
            application_id, update_data, updated_by=current_user.id
        )

        if result is None:
            raise HTTPException(status_code=500, detail="Gagal update feedback")

        # Check for error response from service
        if "error" in result:
            raise HTTPException(
                status_code=result.get("code", 400), detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feedback by application: {e}")
        raise HTTPException(status_code=500, detail=str(e))
