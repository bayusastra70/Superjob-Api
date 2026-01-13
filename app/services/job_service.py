
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.database import get_db_connection
from app.schemas.job import JobCreate, JobStatus

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self):
        pass

    def get_jobs(
        self,
        status: Optional[str] = None,
        department: Optional[str] = None,
        employment_type: Optional[str] = None,
        location: Optional[str] = None,
        working_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get list of jobs with optional filters"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM jobs WHERE 1=1"
            params = []

            if status:
                query += " AND status = %s"
                params.append(status)

            if department:
                query += " AND department = %s"
                params.append(department)

            if employment_type:
                query += " AND employment_type = %s"
                params.append(employment_type)

            if location:
                query += " AND location ILIKE %s"
                params.append(f"%{location}%")

            if working_type:
                query += " AND working_type = %s"
                params.append(working_type)

            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            jobs = cursor.fetchall()

            return jobs

        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []

    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM jobs WHERE id = %s"
            cursor.execute(query, (job_id,))
            job = cursor.fetchone()

            return job

        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None

    

    def create_job(self, job_data: JobCreate, created_by: int) -> Optional[int]:
        """Create new job with all fields from UI flow"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Prioritize company_id from request payload
            company_id = job_data.company_id
            
            # Jika tidak ada di payload, ambil dari user's FK
            if not company_id:
                cursor.execute("SELECT company_id FROM users WHERE id = %s", (created_by,))
                user_row = cursor.fetchone()
                company_id = user_row["company_id"] if user_row else None
            
            if not company_id:
                raise ValueError("company_id is required for job creation")

            # Generate job code if not provided
            job_code = job_data.job_code
            if not job_code:
                # Generate simple job code: DEPT-001
                cursor.execute(
                    """
                SELECT COUNT(*) as count FROM jobs 
                WHERE department = %s AND company_id = %s
                """,
                    (job_data.department, company_id),
                )
                count = cursor.fetchone()["count"]
                dept_code = (job_data.department or "GEN")[:3].upper()
                job_code = f"{dept_code}-{count + 1:03d}"

            # HAPUS employer_id dari insert query karena kolom tidak ada
            insert_query = """
            INSERT INTO jobs (
                job_code, title, department, location, employment_type,
                experience_level, education_requirement, salary_range,
                status, description, requirements, responsibilities, created_by,
                -- New fields from UI flow
                industry, major, working_type, gender_requirement,
                salary_min, salary_max, salary_currency, salary_interval,
                min_age, max_age, qualifications, benefits,
                -- AI Interview settings
                ai_interview_enabled, ai_interview_questions_count,
                ai_interview_duration_seconds, ai_interview_deadline_days,
                ai_interview_questions,
                -- Company relation
                company_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s
            )
            RETURNING id
            """

            # Process enum values
            working_type_val = (
                job_data.working_type.value if job_data.working_type else "onsite"
            )
            gender_val = (
                job_data.gender_requirement.value
                if job_data.gender_requirement
                else "any"
            )
            salary_interval_val = (
                job_data.salary_interval.value
                if job_data.salary_interval
                else "monthly"
            )

            cursor.execute(
                insert_query,
                (
                    job_code,
                    job_data.title,
                    job_data.department,
                    job_data.location,
                    job_data.employment_type,
                    job_data.experience_level,
                    job_data.education_requirement,
                    job_data.salary_range,
                    job_data.status.value,
                    job_data.description,
                    job_data.requirements,
                    job_data.responsibilities,
                    created_by,
                    # New fields from UI flow
                    job_data.industry,
                    job_data.major,
                    working_type_val,
                    gender_val,
                    float(job_data.salary_min) if job_data.salary_min else None,
                    float(job_data.salary_max) if job_data.salary_max else None,
                    job_data.salary_currency or "Rp",
                    salary_interval_val,
                    job_data.min_age,
                    job_data.max_age,
                    job_data.qualifications,
                    job_data.benefits,
                    # AI Interview settings
                    job_data.ai_interview_enabled or False,
                    job_data.ai_interview_questions_count,
                    job_data.ai_interview_duration_seconds,
                    job_data.ai_interview_deadline_days,
                    job_data.ai_interview_questions,
                    # Company relation
                    company_id,  # REQUIRED: from payload or user FK
                ),
            )

            job_id = cursor.fetchone()["id"]
            conn.commit()

            logger.info(f"Job created: {job_id} - {job_data.title} for company {company_id}")
            return job_id

        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return None
        
        
    

    def update_job(self, job_id: int, job_data: Dict[str, Any]) -> bool:
        """Update job"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Build dynamic update query
            set_clauses = []
            params = []

            for field, value in job_data.items():
                if value is not None:
                    # Handle special cases for enums
                    if field in ['working_type', 'gender_requirement', 'salary_interval'] and hasattr(value, 'value'):
                        value = value.value
                    
                    # Prevent updating certain fields if needed
                    if field not in ['created_by', 'employer_id']:  # Jangan update created_by
                        set_clauses.append(f"{field} = %s")
                        params.append(value)

            if not set_clauses:
                return False

            params.append(job_id)
            set_clause = ", ".join(set_clauses)

            query = f"""
            UPDATE jobs 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """

            cursor.execute(query, params)
            conn.commit()

            logger.info(f"Job updated: {job_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            return False

    def delete_job(self, job_id: int) -> bool:
        """Delete job (soft delete by changing status)"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            UPDATE jobs 
            SET status = 'closed', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """

            cursor.execute(query, (job_id,))
            conn.commit()

            logger.info(f"Job marked as closed: {job_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False

    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job statistics"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Count by status
            cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM jobs 
            GROUP BY status
            """)
            status_counts = cursor.fetchall()

            # Count by department
            cursor.execute("""
            SELECT department, COUNT(*) as count 
            FROM jobs 
            WHERE department IS NOT NULL
            GROUP BY department
            """)
            dept_counts = cursor.fetchall()

            # Count by employment type
            cursor.execute("""
            SELECT employment_type, COUNT(*) as count 
            FROM jobs 
            WHERE employment_type IS NOT NULL
            GROUP BY employment_type
            """)
            emp_type_counts = cursor.fetchall()

            # Count by working type
            cursor.execute("""
            SELECT working_type, COUNT(*) as count 
            FROM jobs 
            WHERE working_type IS NOT NULL
            GROUP BY working_type
            """)
            work_type_counts = cursor.fetchall()

            # Count by industry
            cursor.execute("""
            SELECT industry, COUNT(*) as count 
            FROM jobs 
            WHERE industry IS NOT NULL
            GROUP BY industry
            """)
            industry_counts = cursor.fetchall()

            # Recent jobs
            cursor.execute("""
            SELECT COUNT(*) as count 
            FROM jobs 
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            """)
            recent_jobs = cursor.fetchone()["count"]

            # Total jobs
            cursor.execute("SELECT COUNT(*) as count FROM jobs")
            total_jobs = cursor.fetchone()["count"]

            return {
                "total_jobs": total_jobs,
                "status_counts": {row["status"]: row["count"] for row in status_counts},
                "department_counts": {row["department"]: row["count"] for row in dept_counts},
                "employment_type_counts": {row["employment_type"]: row["count"] for row in emp_type_counts},
                "working_type_counts": {row["working_type"]: row["count"] for row in work_type_counts},
                "industry_counts": {row["industry"]: row["count"] for row in industry_counts},
                "recent_jobs": recent_jobs,
            }

        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            return {}
        
    def get_job_with_scoring(self, job_id: int) -> Optional[Dict]:
        """Get job details with scoring information"""
        try:
            # Get basic job data
            job = self.get_job_by_id(job_id)
            if not job:
                return None
            
            # Calculate scoring
            from app.services.job_scoring_service import JobScoringService
            scoring_service = JobScoringService()
            
            try:
                score_data = scoring_service.calculate_job_score(job_id)
                job["scoring"] = score_data
            except Exception as e:
                logger.error(f"Error calculating score for job {job_id}: {str(e)}")
                job["scoring"] = {
                    "overall_score": 0,
                    "quality_label": "Not Calculated",
                    "error": str(e)
                }
            
            return job
            
        except Exception as e:
            logger.error(f"Error getting job with scoring {job_id}: {str(e)}")
            raise
    
    def get_jobs_with_scoring(self, employer_id: int, **filters) -> List[Dict]:
        """Get list of jobs with scoring information"""
        try:
            # Get jobs based on filters
            jobs = self.get_jobs_by_employer(employer_id, **filters)
            
            # Calculate scoring for each job
            from app.services.job_scoring_service import JobScoringService
            scoring_service = JobScoringService()
            
            for job in jobs:
                try:
                    score_data = scoring_service.calculate_job_score(job["id"])
                    job["scoring"] = {
                        "overall_score": score_data["overall_score"],
                        "quality_label": score_data["quality_label"],
                        "completion_rate": score_data["completion_rate"]
                    }
                except Exception as e:
                    logger.error(f"Error calculating score for job {job['id']}: {str(e)}")
                    job["scoring"] = {
                        "overall_score": 0,
                        "quality_label": "Error",
                        "completion_rate": 0
                    }
            
            # Sort by score descending
            jobs.sort(key=lambda x: x["scoring"]["overall_score"], reverse=True)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error getting jobs with scoring: {str(e)}")
            raise