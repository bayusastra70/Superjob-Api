from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from typing import List, Optional
import logging

from app.schemas.application import (
    ApplicationCreate, ApplicationResponse, 
    ApplicationListResponse, ApplicationStatus, InterviewStage
)
from app.services.application_service import ApplicationService
from app.core.security import get_current_user
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/applications", tags=["Applications"])

application_service = ApplicationService()

@router.get("/", response_model=ApplicationListResponse)
async def get_applications(
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    stage: Optional[str] = Query(None, description="Filter by interview stage"),
    search: Optional[str] = Query(None, description="Search in name/email"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get list of applications with filters"""
    try:
        applications = application_service.get_applications(
            job_id=job_id,
            status=status,
            stage=stage,
            search=search,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get total count
        from app.services.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        count_query = "SELECT COUNT(*) as total FROM applications WHERE 1=1"
        params = []
        
        if job_id:
            count_query += " AND job_id = %s"
            params.append(job_id)
        
        if status:
            count_query += " AND application_status = %s"
            params.append(status)
        
        if stage:
            count_query += " AND interview_stage = %s"
            params.append(stage)
        
        if search:
            count_query += " AND (candidate_name ILIKE %s OR candidate_email ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        cursor.close()
        
        return ApplicationListResponse(
            applications=applications,
            total=total,
            filters={
                "job_id": job_id,
                "status": status,
                "stage": stage,
                "search": search
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int = Path(..., description="Application ID"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get application details"""
    try:
        application = application_service.get_application_by_id(application_id)
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return application
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application {application_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=dict)
async def create_application(
    application_data: ApplicationCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create new application"""
    try:
        # For candidates applying, use their own ID
        # For employers adding candidates, they would specify candidate_id differently
        # Here we assume candidate is creating their own application
        application_id = application_service.create_application(
            application_data, 
            candidate_id=current_user.id
        )
        
        if not application_id:
            raise HTTPException(status_code=400, detail="Failed to create application")
        
        return {
            "message": "Application created successfully",
            "application_id": application_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{application_id}/status", response_model=dict)
async def update_application_status(
    application_id: int = Path(..., description="Application ID"),
    new_status: str = Body(..., embed=True),
    new_stage: Optional[str] = Body(None, embed=True),
    reason: Optional[str] = Body(None, embed=True),
    current_user: UserResponse = Depends(get_current_user)
):
    """Update application status and/or interview stage"""
    try:
        # Validate status
        valid_statuses = [s.value for s in ApplicationStatus]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Valid values: {valid_statuses}"
            )
        
        # Validate stage if provided
        if new_stage:
            valid_stages = [s.value for s in InterviewStage]
            if new_stage not in valid_stages:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid stage. Valid values: {valid_stages}"
                )
        
        success = application_service.update_application_status(
            application_id, new_status, new_stage, current_user.id, reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {
            "message": "Application status updated",
            "application_id": application_id,
            "new_status": new_status,
            "new_stage": new_stage
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{application_id}/scores", response_model=dict)
async def update_application_scores(
    application_id: int = Path(..., description="Application ID"),
    fit_score: Optional[float] = Body(None, ge=0, le=100),
    skill_score: Optional[float] = Body(None, ge=0, le=100),
    experience_score: Optional[float] = Body(None, ge=0, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """Update application scores"""
    try:
        success = application_service.update_application_scores(
            application_id, fit_score, skill_score, experience_score
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {
            "message": "Application scores updated",
            "application_id": application_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{application_id}/history", response_model=List[dict])
async def get_application_history(
    application_id: int = Path(..., description="Application ID"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get application status history"""
    try:
        history = application_service.get_application_history(application_id)
        
        if not history:
            # Check if application exists
            app = application_service.get_application_by_id(application_id)
            if not app:
                raise HTTPException(status_code=404, detail="Application not found")
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/dashboard", response_model=dict)
async def get_dashboard_statistics(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get dashboard statistics"""
    try:
        stats = application_service.get_application_statistics()
        
        # Add some quick stats for dashboard
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Today's applications
        cursor.execute("""
        SELECT COUNT(*) as count 
        FROM applications 
        WHERE applied_date = CURRENT_DATE
        """)
        today_apps = cursor.fetchone()['count']
        
        # Applications needing review
        cursor.execute("""
        SELECT COUNT(*) as count 
        FROM applications 
        WHERE application_status IN ('applied', 'in_review')
        """)
        needs_review = cursor.fetchone()['count']
        
        # Upcoming interviews
        cursor.execute("""
        SELECT COUNT(*) as count 
        FROM applications 
        WHERE interview_date >= CURRENT_DATE 
        AND interview_date <= CURRENT_DATE + INTERVAL '7 days'
        """)
        upcoming_interviews = cursor.fetchone()['count']
        
        cursor.close()
        
        return {
            **stats,
            "dashboard_metrics": {
                "today_applications": today_apps,
                "needs_review": needs_review,
                "upcoming_interviews": upcoming_interviews
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/sample-data", response_model=dict)
async def test_sample_data(
    current_user: UserResponse = Depends(get_current_user)
):
    """Test endpoint to verify sample data"""
    try:
        from app.services.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM jobs")
        jobs_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM applications")
        apps_count = cursor.fetchone()['count']
        
        cursor.execute("""
        SELECT 
            application_status, 
            COUNT(*) as count 
        FROM applications 
        GROUP BY application_status
        """)
        status_distribution = cursor.fetchall()
        
        cursor.close()
        
        return {
            "status": "Jobs and Applications system ready",
            "jobs_count": jobs_count,
            "applications_count": apps_count,
            "status_distribution": status_distribution,
            "endpoints_available": {
                "GET /api/v1/jobs": "List jobs",
                "GET /api/v1/jobs/{id}": "Get job details",
                "GET /api/v1/jobs/{id}/applications": "Get job applications",
                "GET /api/v1/applications": "List applications",
                "GET /api/v1/applications/{id}": "Get application details",
                "PUT /api/v1/applications/{id}/status": "Update status",
                "PUT /api/v1/applications/{id}/scores": "Update scores"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))