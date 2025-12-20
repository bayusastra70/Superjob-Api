import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.database import get_db_connection
from app.services.activity_log_service import activity_log_service
from app.schemas.application import ApplicationCreate, ApplicationStatus, InterviewStage

logger = logging.getLogger(__name__)

class ApplicationService:
    def __init__(self):
        pass
    
    def get_applications(
        self,
        job_id: Optional[int] = None,
        status: Optional[str] = None,
        # stage: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get applications with filters and sorting"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
            select 
                j.id job_id
                ,u.full_name as name
                ,j.title as position 
                ,a.candidate_education as education 
                ,u.phone as phone 
                ,u.email as email
                ,a.candidate_linkedin as linkedin 
                ,a.candidate_cv_url as cv 
                ,'Message' as message 
                ,a.application_status as status 
                ,a.fit_score as fit_score
                ,a.created_at
                ,a.updated_at 
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN users u ON a.candidate_id = u.id
            WHERE 1=1
            """
            params = []
            
            if job_id:
                query += " AND a.job_id = %s"
                params.append(job_id)
            
            if status:
                query += " AND a.application_status = %s"
                params.append(status)
            
            # if stage:
            #     query += " AND a.interview_stage = %s"
            #     params.append(stage)
            
            if search:
                query += " AND (u.full_name ILIKE %s OR u.email ILIKE %s)"
                params.extend([f"%{search}%", f"%{search}%"])
            
            # Validate sort column
            valid_sort_columns = ['created_at', 'applied_date', 'overall_score', 'candidate_name']
            if sort_by not in valid_sort_columns:
                sort_by = 'created_at'
            
            # Validate sort order
            sort_order = "DESC" if sort_order.lower() == "desc" else "ASC"
            
            query += f" ORDER BY a.{sort_by} {sort_order} LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            applications = cursor.fetchall()
            
            return applications
            
        except Exception as e:
            logger.error(f"Error getting applications: {e}")
            return []
    
    def get_application_by_id(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Get application by ID"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
            select 
                j.id job_id
                ,u.full_name as name
                ,j.title as position 
                ,a.candidate_education as education 
                ,u.phone as phone 
                ,u.email as email
                ,a.candidate_linkedin as linkedin 
                ,a.candidate_cv_url as cv 
                ,'Message' as message 
                ,a.application_status as status 
                ,a.fit_score as fit_score
                ,a.created_at
                ,a.updated_at 
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN users u ON a.candidate_id = u.id
            WHERE a.id = %s

            """
            
            cursor.execute(query, (application_id,))
            application = cursor.fetchone()
            
            return application
            
        except Exception as e:
            logger.error(f"Error getting application {application_id}: {e}")
            return None
    
    def create_application(self, application_data: ApplicationCreate, candidate_id: int, actor_role: Optional[str] = None, actor_ip=None, actor_user_agent=None) -> Optional[int]:
        """Create new application"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if job exists and capture employer + title for activity
            cursor.execute("SELECT id, title, created_by FROM jobs WHERE id = %s", (application_data.job_id,))
            job_row = cursor.fetchone()
            if not job_row:
                logger.error(f"Job not found: {application_data.job_id}")
                return None
            job_title = job_row.get("title")
            employer_id = job_row.get("created_by") or application_data.job_id
            
            insert_query = """
            INSERT INTO applications (
                job_id, candidate_id, candidate_name, candidate_email,
                candidate_phone, candidate_linkedin, candidate_cv_url,
                candidate_education, candidate_experience_years,
                current_company, current_position, expected_salary,
                notice_period, application_status, interview_stage,
                interview_scheduled_by, interview_date, source, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            cursor.execute(insert_query, (
                application_data.job_id,
                candidate_id,
                application_data.candidate_name,
                application_data.candidate_email,
                application_data.candidate_phone,
                application_data.candidate_linkedin,
                application_data.candidate_cv_url,
                application_data.candidate_education,
                application_data.candidate_experience_years,
                application_data.current_company,
                application_data.current_position,
                application_data.expected_salary,
                application_data.notice_period,
                application_data.application_status.value,
                application_data.interview_stage.value if application_data.interview_stage else None,
                application_data.interview_scheduled_by,
                application_data.interview_date,
                application_data.source,
                application_data.notes
            ))
            
            app_id = cursor.fetchone()['id']
            
            # Create initial history entry
            self._add_application_history(
                app_id, None, 
                None, application_data.application_status.value,
                None, application_data.interview_stage.value if application_data.interview_stage else None,
                "Application created"
            )
            
            conn.commit()
            logger.info(f"Application created: {app_id} - {application_data.candidate_name}")

            activity_log_service.log_new_applicant(
                employer_id=employer_id,
                job_id=application_data.job_id,
                applicant_id=app_id,
                applicant_name=application_data.candidate_name,
                job_title=job_title,
                role=actor_role,
                ip_address=actor_ip,
                user_agent=actor_user_agent,
            )
            return app_id
            
        except Exception as e:
            logger.error(f"Error creating application: {e}")
            return None
    
    def update_application_status(
        self, 
        application_id: int, 
        new_status: str,
        new_stage: Optional[str] = None,
        changed_by: Optional[int] = None,
        reason: Optional[str] = None,
        actor_role: Optional[str] = None,
        actor_ip = None,
        actor_user_agent = None
    ) -> bool:
        """Update application status and stage"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get current status
            cursor.execute("""
            SELECT application_status, interview_stage, job_id, candidate_name 
            FROM applications WHERE id = %s
            """, (application_id,))
            current = cursor.fetchone()
            
            if not current:
                return False
            
            # Update application
            update_query = """
            UPDATE applications 
            SET application_status = %s, 
                interview_stage = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            cursor.execute(update_query, (
                new_status,
                new_stage,
                application_id
            ))
            
            # Add to history
            self._add_application_history(
                application_id, changed_by,
                current['application_status'], new_status,
                current['interview_stage'], new_stage,
                reason or "Status updated"
            )
            
            conn.commit()
            logger.info(f"Application {application_id} status updated to {new_status}")

            employer_id = None
            job_title = None
            if current.get("job_id"):
                cursor.execute("SELECT created_by, title FROM jobs WHERE id = %s", (current["job_id"],))
                job_info = cursor.fetchone()
                if job_info:
                    employer_id = job_info.get("created_by")
                    job_title = job_info.get("title")

            activity_log_service.log_status_update(
                employer_id=employer_id or current.get("job_id"),
                job_id=current.get("job_id"),
                applicant_id=application_id,
                applicant_name=current.get("candidate_name"),
                old_status=current.get("application_status"),
                new_status=new_status,
                role=actor_role,
                ip_address=actor_ip,
                user_agent=actor_user_agent,
            )
            return True
            
        except Exception as e:
            logger.error(f"Error updating application status: {e}")
            return False
    
    def update_application_scores(
        self,
        application_id: int,
        fit_score: Optional[float] = None,
        skill_score: Optional[float] = None,
        experience_score: Optional[float] = None
    ) -> bool:
        """Update application scores"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            set_clauses = []
            params = []
            
            if fit_score is not None:
                set_clauses.append("fit_score = %s")
                params.append(fit_score)
            
            if skill_score is not None:
                set_clauses.append("skill_score = %s")
                params.append(skill_score)
            
            if experience_score is not None:
                set_clauses.append("experience_score = %s")
                params.append(experience_score)
            
            # Calculate overall score if all scores provided
            if fit_score is not None and skill_score is not None and experience_score is not None:
                overall_score = (fit_score * 0.4 + skill_score * 0.4 + experience_score * 0.2)
                set_clauses.append("overall_score = %s")
                params.append(round(overall_score, 2))
            
            if not set_clauses:
                return False
            
            params.append(application_id)
            set_clause = ", ".join(set_clauses)
            
            query = f"""
            UPDATE applications 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            cursor.execute(query, params)
            conn.commit()
            
            logger.info(f"Application {application_id} scores updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating application scores: {e}")
            return False
    
    def get_application_history(self, application_id: int) -> List[Dict[str, Any]]:
        """Get application status history"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT h.*, u.email as changed_by_email
            FROM application_history h
            LEFT JOIN users u ON h.changed_by = u.id
            WHERE h.application_id = %s
            ORDER BY h.change_date DESC
            """
            
            cursor.execute(query, (application_id,))
            history = cursor.fetchall()
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting application history: {e}")
            return []
    
    def _add_application_history(
        self,
        application_id: int,
        changed_by: Optional[int],
        previous_status: Optional[str],
        new_status: Optional[str],
        previous_stage: Optional[str],
        new_stage: Optional[str],
        change_reason: str
    ):
        """Add entry to application history"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO application_history (
                application_id, changed_by, previous_status,
                new_status, previous_stage, new_stage, change_reason
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                application_id, changed_by, previous_status,
                new_status, previous_stage, new_stage, change_reason
            ))
            
        except Exception as e:
            logger.error(f"Error adding application history: {e}")
    
    def get_application_statistics(self, job_id: Optional[int] = None) -> Dict[str, Any]:
        """Get application statistics"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            where_clause = "WHERE 1=1"
            params = []
            
            if job_id:
                where_clause += " AND job_id = %s"
                params.append(job_id)
            
            # Count by status
            cursor.execute(f"""
            SELECT application_status, COUNT(*) as count 
            FROM applications 
            {where_clause}
            GROUP BY application_status
            """, params)
            status_counts = cursor.fetchall()
            
            # Count by stage
            cursor.execute(f"""
            SELECT interview_stage, COUNT(*) as count 
            FROM applications 
            {where_clause} AND interview_stage IS NOT NULL
            GROUP BY interview_stage
            """, params)
            stage_counts = cursor.fetchall()
            
            # Recent applications
            cursor.execute(f"""
            SELECT COUNT(*) as count 
            FROM applications 
            WHERE applied_date >= CURRENT_DATE - INTERVAL '7 days'
            {'' if not job_id else ' AND job_id = %s'}
            """, params if job_id else [])
            recent_apps = cursor.fetchone()['count']
            
            # Average scores
            cursor.execute(f"""
            SELECT 
                AVG(fit_score) as avg_fit,
                AVG(skill_score) as avg_skill,
                AVG(experience_score) as avg_exp,
                AVG(overall_score) as avg_overall
            FROM applications 
            {where_clause} AND overall_score IS NOT NULL
            """, params)
            avg_scores = cursor.fetchone()
            
            return {
                "status_counts": status_counts,
                "stage_counts": stage_counts,
                "recent_applications": recent_apps,
                "average_scores": avg_scores
            }
            
        except Exception as e:
            logger.error(f"Error getting application statistics: {e}")
            return {}
