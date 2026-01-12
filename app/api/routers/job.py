
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request
from typing import Optional, List, Dict
import logging
from decimal import Decimal

from app.schemas.job import JobCreate, JobResponse, JobListResponse, JobUpdate
from app.schemas.application import ApplicationListResponse
from app.services.job_service import JobService
from app.services.application_service import ApplicationService
from app.services.database import get_db_connection
from app.core.security import get_current_user
from app.schemas.user import UserResponse
from app.services.activity_log_service import activity_log_service
from app.schemas.job_performance import JobPerformanceItem, JobPerformanceResponse

from app.utils.response import (
    success_response,
    unauthorized_response,
    internal_server_error_response,
    not_found_response,
    bad_request_response,
    created_response
)

from app.schemas.response import BaseResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["Jobs (Unified - Integer ID)"])

job_service = JobService()
application_service = ApplicationService()


@router.get(
    "/employers/{employer_id}/job-performance",
    response_model=BaseResponse[JobPerformanceResponse],
    summary="Get Job Performance Metrics",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "Code": 200,
                        "IsSuccess": True,
                        "Message": "Success",
                        "Data": {}
                    }
                }
            }
        },
        422: { 
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "is_success": False,
                        "message": "Validation Error",
                        "data": {}
                    }
                }
            }
        }
    },
)
async def get_job_performance(
    employer_id: int = Path(
        ...,
        description="ID Employer",
        example=8,
    ),
    status: Optional[str] = Query(
        None,
        pattern="^(active|draft|closed)$",
        description="Filter status job",
    ),
    sort_by: str = Query(
        "views",
        pattern="^(views|applicants|apply_rate|status)$",
        description="Field untuk sorting",
    ),
    order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="Urutan sorting",
    ),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(20, ge=1, le=100, description="Jumlah item per halaman"),
    current_user: UserResponse = Depends(get_current_user),
) -> BaseResponse[JobPerformanceResponse]:
    
    try:
        # Hitung offset
        offset = (page - 1) * limit

        # Ambil data dari database
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query untuk mendapatkan total
            count_query = """
            SELECT COUNT(*) as total 
            FROM jobs 
            WHERE created_by = %s
            """
            params = [employer_id]

            if status:
                status_map = {"active": "published", "draft": "draft", "closed": "archived"}
                count_query += " AND status = %s"
                params.append(status_map.get(status, status))

            cursor.execute(count_query, params)
            total = cursor.fetchone()["total"]

            # Hitung total pages
            total_pages = (total + limit - 1) // limit if limit > 0 else 0

            # Query untuk mendapatkan data dengan pagination dan sorting
            query = """
            SELECT 
                j.id as job_id,
                j.title as job_title,
                COALESCE(v.views_count, 0) as views_count,
                COALESCE(a.applicants_count, 0) as applicants_count,
                CASE 
                    WHEN COALESCE(v.views_count, 0) > 0 
                    THEN ROUND((COALESCE(a.applicants_count, 0) * 100.0 / v.views_count), 2)
                    ELSE 0 
                END as apply_rate,
                j.status,
                j.updated_at
            FROM jobs j
            LEFT JOIN (
                SELECT job_id, COUNT(*) as views_count
                FROM job_views
                GROUP BY job_id
            ) v ON j.id = v.job_id
            LEFT JOIN (
                SELECT job_id, COUNT(*) as applicants_count
                FROM applications
                WHERE job_id IS NOT NULL
                GROUP BY job_id
            ) a ON j.id = a.job_id
            WHERE j.created_by = %s
            """

            query_params = [employer_id]

            # Tambahkan filter status
            if status:
                status_map = {"active": "published", "draft": "draft", "closed": "archived"}
                query += " AND j.status = %s"
                query_params.append(status_map.get(status, status))

            # Tambahkan sorting
            sort_map = {
                "views": "views_count",
                "applicants": "applicants_count",
                "apply_rate": "apply_rate",
                "status": "status",
            }

            query += f" ORDER BY {sort_map[sort_by]} {order}"

            # Tambahkan pagination
            query += " LIMIT %s OFFSET %s"
            query_params.extend([limit, offset])

            cursor.execute(query, query_params)
            rows = cursor.fetchall()

        finally:
            # Pastikan resources ditutup
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        # Format data response
        items = []
        for row in rows:
            items.append(
                JobPerformanceItem(
                    job_id=str(row["job_id"]),
                    job_title=row["job_title"],
                    views_count=row["views_count"],
                    applicants_count=row["applicants_count"],
                    apply_rate=float(row["apply_rate"]),
                    status=row["status"],
                    updated_at=row["updated_at"],
                )
            )

        # Jika tidak ada data
        # Format data response
        items = []
        for row in rows:
            items.append(
                JobPerformanceItem(
                    job_id=str(row["job_id"]),
                    job_title=row["job_title"],
                    views_count=row["views_count"],
                    applicants_count=row["applicants_count"],
                    apply_rate=float(row["apply_rate"]),
                    status=row["status"],
                    updated_at=row["updated_at"],
                )
            )

        # Tentukan message berdasarkan kondisi
        message = "Success"
        if total == 0:
            message = "No job postings found for this employer"
        elif len(items) == 0 and page > 1:
            message = f"No data on page {page}"
        
        data_message = None
        if total == 0:
            data_message = "Belum ada job posting untuk employer ini"

        jobPerformanceResponse = JobPerformanceResponse(
            items=items,
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,  # ✅ Tambahkan total_pages
            sort_by=sort_by,
            order=order,
            status_filter=status,
            message=data_message,
            meta={
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "prev_page": page - 1 if page > 1 else None,
            },
        )

        return success_response(
            data=jobPerformanceResponse,
            message=message
        )

    except Exception as e:
        logger.error(f"Error getting job performance for employer {employer_id}: {e}")
        return internal_server_error_response(message=f"{str(e)} ",raise_exception=False)


@router.get(
    "/",
    response_model=BaseResponse[JobListResponse],
    summary="List Job Positions",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "Code": 200,
                        "IsSuccess": True,
                        "Message": "Success",
                        "Data": {}
                    }
                }
            }
        },
        422: { 
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "is_success": False,
                        "message": "Validation Error",
                        "data": {}
                    }
                }
            }
        }
    },
)
async def get_jobs(
    status: Optional[str] = Query(
        None,
        description="Filter by status (open, closed, draft, published, archived)",
    ),
    department: Optional[str] = Query(
        None,
        description="Filter by department",
    ),
    employment_type: Optional[str] = Query(
        None,
        description="Filter by employment type",
    ),
    location: Optional[str] = Query(
        None,
        description="Filter by location",
    ),
    working_type: Optional[str] = Query(
        None,
        description="Filter by working type (onsite, remote, hybrid)",
    ),
    limit: int = Query(50, ge=1, le=100, description="Jumlah item per halaman"),
    offset: int = Query(0, ge=0, description="Offset untuk pagination"),
    current_user: UserResponse = Depends(get_current_user),
) -> BaseResponse[JobListResponse]:
    """Get list of job positions dengan semua field dari database"""
    try:
        # Panggil service dengan parameter yang sama
        jobs = job_service.get_jobs(
            status=status, 
            department=department, 
            employment_type=employment_type,
            location=location,
            working_type=working_type,
            limit=limit, 
            offset=offset
        )

        # Get total count untuk pagination - PERBAIKAN: TUTUP CONNECTION
        conn = None
        cursor = None
        total = 0
        
        try:
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

            if employment_type:
                count_query += " AND employment_type = %s"
                params.append(employment_type)

            if location:
                count_query += " AND location ILIKE %s"
                params.append(f"%{location}%")

            if working_type:
                count_query += " AND working_type = %s"
                params.append(working_type)

            cursor.execute(count_query, params)
            total = cursor.fetchone()["total"]
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        # Buat response sesuai dengan schema yang ada
        jobListResponse = JobListResponse(jobs=jobs, total=total)
    
        # Tentukan message berdasarkan kondisi
        message = "Job list retrieved successfully"
        if total == 0:
            message = "No jobs found"
        elif len(jobs) == 0 and offset > 0:
            # Jika ada offset tapi tidak ada data di halaman itu
            message = f"No more jobs available from offset {offset}"
        
        return success_response(
            data=jobListResponse,
            message=message
        )

    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return internal_server_error_response(message=f"{e} ",raise_exception=False)


@router.get(
    "/{job_id}",
    response_model=BaseResponse[JobResponse],
    summary="Get Job Details",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "Code": 200,
                        "IsSuccess": True,
                        "Message": "Success",
                        "Data": {}
                    }
                }
            }
        },
        422: { 
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "is_success": False,
                        "message": "Validation Error",
                        "data": {}
                    }
                }
            }
        }
    },
)
async def get_job(
    job_id: int = Path(
        ...,
        description="Job ID (Integer)",
        example=1,
    ),
    current_user: UserResponse = Depends(get_current_user),
) -> BaseResponse[JobResponse]:
    
    try:
        job = job_service.get_job_by_id(job_id)
        logger.info(f"JOB AFTER SERVICE => {job}");
        if not job:
            # raise HTTPException(status_code=404, detail="Job not found")
            return not_found_response(message=f"Job with ID {job_id} Not Found",raise_exception=False)

        # return job
        return success_response(
                data=job,
                message="Success"
            )

    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        return internal_server_error_response(
                message=f"{e} ",
                raise_exception=False
            )


@router.post(
    "/",
    response_model=BaseResponse[dict],
    summary="Create Job",
    responses={
        200: { 
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "code": 201,
                        "is_success": True,
                        "message": "Job created successfully",
                        "data": {
                            "job_id": 123
                        }
                    }
                }
            }
        },
        422: { 
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "is_success": False,
                        "message": "Validation Error",
                        "data": {}
                    }
                }
            }
        }
    },
)
async def create_job(
    job_data: JobCreate, current_user: UserResponse = Depends(get_current_user)
) -> BaseResponse[dict]:
    
    try:
        job_id = job_service.create_job(job_data, current_user.id)

        if not job_id:
            # raise HTTPException(status_code=400, detail="Failed to create job")
            return bad_request_response(message=f"Failed to create job",raise_exception=False)
            
        # return {"message": "Job created successfully", "job_id": job_id}
        return created_response(
                data={"job_id": job_id},
            )

    except Exception as e:
        logger.error(f"Error creating job: {e}")
        # raise HTTPException(status_code=500, detail=str(e))
        return internal_server_error_response(message=f"{e} ",raise_exception=False)


@router.put(
    "/{job_id}",
    response_model=BaseResponse[dict],
    summary="Update Job Position",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "Code": 200,
                        "IsSuccess": True,
                        "Message": "Success",
                        "Data": {}
                    }
                }
            }
        },
        422: { 
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "is_success": False,
                        "message": "Validation Error",
                        "data": {}
                    }
                }
            }
        }
    },
)
async def update_job(
    request: Request,
    job_id: int = Path(
        ...,
        description="Job ID (Integer)",
        example=1,
    ),
    job_data: Optional[JobUpdate] = None,
    current_user: UserResponse = Depends(get_current_user),
)-> BaseResponse[dict]:
    try:
        # Get old job data first (untuk check status berubah ke published)
        old_job = job_service.get_job_by_id(job_id)

        if not old_job:
            return not_found_response(
                message=f"Job with ID {job_id} not found",
                raise_exception=False
            )
        
        old_status = old_job.get("status") if old_job else None

        if job_data:
            update_data = job_data.dict(exclude_unset=True)
        else:
            update_data = {}

        if not update_data:
            return bad_request_response(
                message="No data to update",
                raise_exception=False
            )

        success = job_service.update_job(job_id, update_data)

        if not success:
            return not_found_response(message=f"Job not found or update failed",raise_exception=False)

        # Log jika status berubah ke published
        new_status = update_data.get("status")
        job_title = update_data.get("title") or old_job.get("title")

        # Log perubahan status job (semua perubahan status)
        if new_status and new_status != old_status:
            if new_status == "published" and old_status != "published":
                # Log published khusus
                activity_log_service.log_job_published(
                    employer_id=current_user.id,
                    job_id=job_id,
                    job_title=job_title,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    role="employer",
                )
                return success_response(
                    data={"job_id": job_id},
                    message="Job published successfully"
                )
            else:
                # Log perubahan status lainnya
                activity_log_service.log_job_status_changed(
                    employer_id=current_user.id,
                    job_id=job_id,
                    job_title=job_title,
                    old_status=old_status,
                    new_status=new_status,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    role="employer",
                )

        message = "Job updated successfully"
        if new_status:
            message = f"Job updated successfully (status: {new_status})"
        
        return success_response(
            data={"job_id": job_id},
            message=message
        )

    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        return internal_server_error_response(message=f"{str(e)}",raise_exception=False)


@router.delete(
    "/{job_id}",
    response_model=BaseResponse[dict],
    summary="Delete Job Position",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "Code": 200,
                        "IsSuccess": True,
                        "Message": "Success",
                        "Data": {}
                    }
                }
            }
        },
        422: { 
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "is_success": False,
                        "message": "Validation Error",
                        "data": {}
                    }
                }
            }
        }
    },
)
async def delete_job(
    job_id: int = Path(
        ...,
        description="Job ID (Integer)",
        example=1,
    ),
    current_user: UserResponse = Depends(get_current_user),
) -> BaseResponse[dict]:
    try:
        success = job_service.delete_job(job_id)

        if not success:
            return not_found_response(message=f"Job not found")

        return success_response(
            data={"job_id": job_id},
            message="Delete Success"
        )

    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        return internal_server_error_response(message=f"{e}")


@router.get(
    "/{job_id}/applications",
    response_model=BaseResponse[ApplicationListResponse],
    summary="Get Job Applications",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "Code": 200,
                        "IsSuccess": True,
                        "Message": "Success",
                        "Data": {}
                    }
                }
            }
        },
        422: { 
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "is_success": False,
                        "message": "Validation Error",
                        "data": {}
                    }
                }
            }
        }
    },
)
async def get_job_applications(
    job_id: int = Path(
        ...,
        description="Job ID (Integer)",
        example=1,
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by status",
    ),
    stage: Optional[str] = Query(
        None,
        description="Filter by interview stage",
    ),
    search: Optional[str] = Query(
        None,
        description="Search in name/email",
    ),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc/desc"),
    current_user: UserResponse = Depends(get_current_user),
) -> BaseResponse[ApplicationListResponse]:
    
    try:
        applications = application_service.get_applications(
            job_id=job_id,
            status=status,
            stage=stage,
            search=search,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        conn = None
        cursor = None
        total = 0
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            count_query = "SELECT COUNT(*) as total FROM applications WHERE job_id = %s"
            params = [job_id]

            if status:
                count_query += " AND application_status = %s"
                params.append(status)

            cursor.execute(count_query, params)
            total = cursor.fetchone()["total"]
            
        finally:
            
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        applicationListResponse = ApplicationListResponse(
            applications=applications,
            total=total,
            filters={
                "job_id": job_id,
                "status": status,
                "stage": stage,
                "search": search,
            },
        )

        return success_response(
            data=applicationListResponse,
        )

    except Exception as e:
        logger.error(f"Error getting job applications: {e}")
        return internal_server_error_response(message=f"{e}")


@router.get(
    "/{job_id}/statistics",
    response_model=BaseResponse[dict],
    summary="Get Job Statistics",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "Code": 200,
                        "IsSuccess": True,
                        "Message": "Success",
                        "Data": {}
                    }
                }
            }
        },
        422: { 
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "is_success": False,
                        "message": "Validation Error",
                        "data": {}
                    }
                }
            }
        }
    },
)
async def get_job_statistics(
    job_id: int = Path(
        ...,
        description="Job ID (Integer)",
        example=1,
    ),
    current_user: UserResponse = Depends(get_current_user),
) -> BaseResponse[dict]:
    try:
        # Get job details first
        job = job_service.get_job_by_id(job_id)
        if not job:
            return not_found_response(message=f"Job not found")

        # Get application statistics
        stats = application_service.get_application_statistics(job_id)

        # return {"job": job, "statistics": stats}
        return success_response(
            data={"job": job, "statistics": stats},
        )

    except Exception as e:
        logger.error(f"Error getting job statistics: {e}")
        return internal_server_error_response(message=f"{str(e)}")


@router.get(
    "/statistics/overall",
    response_model=BaseResponse[dict],
    summary="Get Overall Statistics",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "Code": 200,
                        "IsSuccess": True,
                        "Message": "Success",
                        "Data": {}
                    }
                }
            }
        },
        422: { 
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "is_success": False,
                        "message": "Validation Error",
                        "data": {}
                    }
                }
            }
        }
    },
)
async def get_overall_statistics(
    current_user: UserResponse = Depends(get_current_user),
)-> BaseResponse[dict]:
    
    try:
        job_stats = job_service.get_job_statistics()
        app_stats = application_service.get_application_statistics()

        # return {"job_statistics": job_stats, "application_statistics": app_stats}
        return success_response(
            data={"job_statistics": job_stats, "application_statistics": app_stats},
        )

    except Exception as e:
        logger.error(f"Error getting overall statistics: {e}")
        return internal_server_error_response(message=f"{str(e)}")


@router.get(
    "/search/filters",
    response_model=BaseResponse[Dict[str, List[str]]],
    summary="Get Available Filters",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "Code": 200,
                        "IsSuccess": True,
                        "Message": "Success",
                        "Data": {}
                    }
                }
            }
        },
        422: { 
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "is_success": False,
                        "message": "Validation Error",
                        "data": {}
                    }
                }
            }
        }
    },
)
async def get_available_filters(
    current_user: UserResponse = Depends(get_current_user),
)-> BaseResponse[Dict[str, List[str]]]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        filters = {}

        # Get unique departments
        cursor.execute("SELECT DISTINCT department FROM jobs WHERE department IS NOT NULL ORDER BY department")
        filters["departments"] = [row["department"] for row in cursor.fetchall()]

        # Get unique locations
        cursor.execute("SELECT DISTINCT location FROM jobs WHERE location IS NOT NULL ORDER BY location")
        filters["locations"] = [row["location"] for row in cursor.fetchall()]

        # Get unique employment types
        cursor.execute("SELECT DISTINCT employment_type FROM jobs WHERE employment_type IS NOT NULL ORDER BY employment_type")
        filters["employment_types"] = [row["employment_type"] for row in cursor.fetchall()]

        # Get unique working types
        cursor.execute("SELECT DISTINCT working_type FROM jobs WHERE working_type IS NOT NULL ORDER BY working_type")
        filters["working_types"] = [row["working_type"] for row in cursor.fetchall()]

        # Get unique industries
        cursor.execute("SELECT DISTINCT industry FROM jobs WHERE industry IS NOT NULL ORDER BY industry")
        filters["industries"] = [row["industry"] for row in cursor.fetchall()]

        # Get unique statuses
        cursor.execute("SELECT DISTINCT status FROM jobs ORDER BY status")
        filters["statuses"] = [row["status"] for row in cursor.fetchall()]

        total_filters = sum(len(values) for values in filters.values())
        message = f"Retrieved {total_filters} filter options"
        if total_filters == 0:
            message = "No filter options available"

        # Return success response - logic tetap sama
        return success_response(
            data=filters,
            message=message
        )

    except Exception as e:
        logger.error(f"Error getting available filters: {e}")
        return internal_server_error_response(message=f"{str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()