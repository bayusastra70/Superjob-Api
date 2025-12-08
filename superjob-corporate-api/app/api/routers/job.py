from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
import logging

from app.schemas.job import JobCreate, JobResponse, JobListResponse
from app.schemas.application import ApplicationListResponse
from app.services.job_service import JobService
from app.services.application_service import ApplicationService
from app.core.security import get_current_user
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["Jobs"])

job_service = JobService()
application_service = ApplicationService()

@router.get("/", response_model=JobListResponse)
async def get_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get list of job positions"""
    try:
        jobs = job_service.get_jobs(status, department, limit, offset)
        
        # Get total count for pagination
        conn = get_db_connection()
        cursor = conn.cursor()
        count_query = "SELECT COUNT(*) as total FROM jobs WHERE 1=1"
        params = []
        
        if status:
            count_query += " AND status = %s"
            params.append(status)
        
        if department:
            count_query += " AND department = %s"
            params.append(department)
        
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        cursor.close()
        
        return JobListResponse(jobs=jobs, total=total)
        
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int = Path(..., description="Job ID"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get job details"""
    try:
        job = job_service.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=dict)
async def create_job(
    job_data: JobCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create new job position"""
    try:
        job_id = job_service.create_job(job_data, current_user.id)
        
        if not job_id:
            raise HTTPException(status_code=400, detail="Failed to create job")
        
        return {
            "message": "Job created successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{job_id}", response_model=dict)
async def update_job(
    job_id: int = Path(..., description="Job ID"),
    job_data: JobCreate = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update job position"""
    try:
        # Convert Pydantic model to dict (exclude unset fields)
        update_data = job_data.dict(exclude_unset=True) if job_data else {}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        success = job_service.update_job(job_id, update_data)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or update failed")
        
        return {
            "message": "Job updated successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{job_id}", response_model=dict)
async def delete_job(
    job_id: int = Path(..., description="Job ID"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete job position (mark as closed)"""
    try:
        success = job_service.delete_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "message": "Job marked as closed",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}/applications", response_model=ApplicationListResponse)
async def get_job_applications(
    job_id: int = Path(..., description="Job ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    stage: Optional[str] = Query(None, description="Filter by interview stage"),
    search: Optional[str] = Query(None, description="Search in name/email"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get applications for a specific job"""
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
        conn = get_db_connection()
        cursor = conn.cursor()
        count_query = "SELECT COUNT(*) as total FROM applications WHERE job_id = %s"
        params = [job_id]
        
        if status:
            count_query += " AND application_status = %s"
            params.append(status)
        
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
        logger.error(f"Error getting job applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}/statistics", response_model=dict)
async def get_job_statistics(
    job_id: int = Path(..., description="Job ID"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get statistics for a job"""
    try:
        # Get job details first
        job = job_service.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get application statistics
        stats = application_service.get_application_statistics(job_id)
        
        return {
            "job": job,
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/overall", response_model=dict)
async def get_overall_statistics(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get overall job and application statistics"""
    try:
        job_stats = job_service.get_job_statistics()
        app_stats = application_service.get_application_statistics()
        
        return {
            "job_statistics": job_stats,
            "application_statistics": app_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting overall statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))