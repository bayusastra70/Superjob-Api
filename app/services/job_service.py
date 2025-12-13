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
        limit: int = 50,
        offset: int = 0
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
        """Create new job"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Generate job code if not provided
            job_code = job_data.job_code
            if not job_code:
                # Generate simple job code: DEPT-001
                cursor.execute("""
                SELECT COUNT(*) as count FROM jobs 
                WHERE department = %s
                """, (job_data.department,))
                count = cursor.fetchone()['count']
                dept_code = (job_data.department or "GEN")[:3].upper()
                job_code = f"{dept_code}-{count+1:03d}"
            
            insert_query = """
            INSERT INTO jobs (
                job_code, title, department, location, employment_type,
                experience_level, education_requirement, salary_range,
                status, description, requirements, responsibilities, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            cursor.execute(insert_query, (
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
                created_by
            ))
            
            job_id = cursor.fetchone()['id']
            conn.commit()
            
            logger.info(f"Job created: {job_id} - {job_data.title}")
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
            
            # Recent jobs
            cursor.execute("""
            SELECT COUNT(*) as count 
            FROM jobs 
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            """)
            recent_jobs = cursor.fetchone()['count']
            
            return {
                "status_counts": status_counts,
                "department_counts": dept_counts,
                "recent_jobs": recent_jobs
            }
            
        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            return {}