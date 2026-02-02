from loguru import logger
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.database import get_db_connection, release_connection
from app.services.activity_log_service import activity_log_service
from app.schemas.application import ApplicationCreate
from fastapi import UploadFile
from app.services.application_file_service import ApplicationFileService



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
                a.id as id
                ,j.id as job_id
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
                ,a.notes as notes
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
                a.id as id
                ,j.id as job_id
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
                ,a.notes as notes
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
        

    async def create_application_with_files(
        self,
        job_id: int,
        coverletter: Optional[str],
        portfolio_link: Optional[str],
        location: Optional[str],
        cv_file: Optional[UploadFile],  # Changed to Optional
        cv_link: Optional[str],         # New parameter
        portfolio_file: Optional[UploadFile],
        candidate_id: int,
        actor_role: Optional[str] = None,
        actor_ip: Optional[str] = None,
        actor_user_agent: Optional[str] = None
    ) -> Optional[int]:
        """Create application with file uploads - commit first approach"""
        import traceback
        
        conn = None
        cursor = None
        try:
            logger.info(f"Starting application creation for candidate_id: {candidate_id}, job_id: {job_id}")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            logger.debug("Database connection acquired")
            
            # ===== 1. GET USER DATA =====
            cursor.execute(
                "SELECT full_name, whatsapp_number FROM users WHERE id = %s", 
                (candidate_id,)
            )
            user_row = cursor.fetchone()
            
            logger.debug(f"User data retrieved: {user_row}")
            
            if not user_row:
                logger.warning(f"User not found: {candidate_id}")
                return None
            
            # ===== 2. CREATE APPLICATION (COMMIT FIRST) =====
            insert_query = """
            INSERT INTO applications (
                job_id, candidate_id, address, coverletter, portofolio,
                application_status, source
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            cursor.execute(insert_query, (
                job_id,
                candidate_id,
                location,
                coverletter,
                portfolio_link,  # Portfolio text/link
                'applied',
                'website'
            ))
            
            application_id = cursor.fetchone()['id']
            
            # COMMIT NOW - ensure application exists in DB before file upload
            conn.commit()
            logger.info(f"✅ Application record committed to DB: {application_id}")
            
            # ===== 3. HANDLE CV (File or Link) =====
            file_service = ApplicationFileService()
            
            # CV File Upload
            if cv_file and cv_file.filename:
                logger.info(f"Uploading CV file: {cv_file.filename}")
                try:
                    cv_upload_response = await file_service.upload_file(
                        application_id=application_id,
                        file=cv_file,
                        original_filename=cv_file.filename,
                        stored_filename=f"cv_{candidate_id}",
                        file_type="cv",
                        uploader_id=candidate_id,
                        uploader_ip=actor_ip,
                        uploader_user_agent=actor_user_agent
                    )
                    
                    if cv_upload_response:
                        logger.info(f"✅ CV file uploaded successfully: {cv_upload_response.file_url}")
                    else:
                        logger.warning("CV file upload returned no response")
                except Exception as upload_error:
                    logger.error(f"❌ CV file upload failed: {upload_error}")
                    # Continue without CV file
            
            # CV Link (Save as application_files with type "cv_link")
            elif cv_link:
                logger.info(f"Saving CV link: {cv_link}")
                try:
                    # Save CV link to application_files as a special type
                    cursor.execute("""
                    INSERT INTO application_files (
                        application_id, 
                        file_name, 
                        file_url,
                        upload_status,
                        file_type,
                        created_by,
                        uploader_ip,
                        uploader_user_agent
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        application_id,
                        "cv_link",
                        cv_link,
                        "completed",
                        "cv_link",  # Special type for CV links
                        candidate_id,
                        actor_ip,
                        actor_user_agent
                    ))
                    conn.commit()
                    logger.info(f"✅ CV link saved to application_files")
                except Exception as link_error:
                    logger.error(f"❌ Failed to save CV link: {link_error}")
            
            # ===== 4. HANDLE PORTFOLIO FILE =====
            if portfolio_file and portfolio_file.filename:
                logger.info(f"Uploading portfolio file: {portfolio_file.filename}")
                try:
                    portfolio_upload_response = await file_service.upload_file(
                        application_id=application_id,
                        file=portfolio_file,
                        original_filename=portfolio_file.filename,
                        stored_filename=f"portfolio_{candidate_id}",
                        file_type="portfolio",
                        uploader_id=candidate_id,
                        uploader_ip=actor_ip,
                        uploader_user_agent=actor_user_agent
                    )
                    
                    if portfolio_upload_response:
                        logger.info(f"✅ Portfolio file uploaded successfully: {portfolio_upload_response.file_url}")
                    else:
                        logger.warning("Portfolio file upload returned no response")
                except Exception as upload_error:
                    logger.error(f"❌ Portfolio file upload failed: {upload_error}")
            
            # ===== 5. CREATE APPLICATION HISTORY =====
            try:
                self._add_application_history(
                    application_id, None, None, 'applied',
                    None, None, "Application created via form"
                )
                logger.debug("Application history created")
            except Exception as history_error:
                logger.error(f"❌ Failed to create application history: {history_error}")
            
            # ===== 6. LOG ACTIVITY =====
            try:
                cursor.execute(
                    "SELECT title, created_by FROM jobs WHERE id = %s", 
                    (job_id,)
                )
                job_row = cursor.fetchone()
                logger.debug(f"Job data: {job_row}")
            except Exception as log_error:
                logger.error(f"❌ Failed to log activity: {log_error}")
            
            logger.info(f"🎉 Application {application_id} created successfully")
            
            return application_id
            
        except Exception as e:
            logger.error(f"❌ Critical error creating application: {type(e).__name__}: {str(e)}")
            logger.error(f"📝 Traceback:\n{traceback.format_exc()}")
            
            if conn:
                try:
                    conn.rollback()
                    logger.debug("Transaction rolled back")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")
            
            return None
        
        finally:
            if cursor:
                cursor.close()
                logger.debug("Cursor closed")
            
            if conn:
                try:
                    conn.autocommit = True
                    release_connection(conn)
                    logger.debug("Connection released to pool")
                except Exception as release_error:
                    logger.error(f"Failed to release connection: {release_error}")
            
    
    
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

    def get_my_applications(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get applications for a specific user (candidate) with optional status filter"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT
                a.id as id
                ,j.id as job_id
                ,u.full_name as name
                ,j.title as position
                ,a.candidate_education as education
                ,u.phone as phone
                ,u.email as email
                ,a.candidate_linkedin as linkedin
                ,a.candidate_cv_url as cv
                ,a.application_status as status
                ,a.fit_score as fit_score
                ,a.notes as notes
                ,a.created_at
                ,a.updated_at
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN users u ON a.candidate_id = u.id
            WHERE a.candidate_id = %s
            """
            params = [user_id]

            if status:
                query += " AND a.application_status = %s"
                params.append(status)

            query += " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            applications = cursor.fetchall()

            return applications

        except Exception as e:
            logger.error(f"Error getting my applications for user {user_id}: {e}")
            return []

    def count_my_applications(
        self,
        user_id: int,
        status: Optional[str] = None
    ) -> int:
        """Count applications for a specific user with optional status filter"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = "SELECT COUNT(*) as total FROM applications WHERE candidate_id = %s"
            params = [user_id]

            if status:
                query += " AND application_status = %s"
                params.append(status)

            cursor.execute(query, params)
            result = cursor.fetchone()
            return result["total"] if result else 0

        except Exception as e:
            logger.error(f"Error counting my applications for user {user_id}: {e}")
            return 0
