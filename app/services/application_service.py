from loguru import logger
from typing import List, Dict, Any, Optional, Tuple
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
        statuses: Optional[List[str]] = None,
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
            SELECT                  
                a.id as id 
                ,j.id as job_id                 
                ,u.full_name as name                 
                ,j.title as position                  
                ,a.candidate_education as education                  
                ,u.phone as phone                  
                ,u.email as email                 
                ,u.linkedin_url  as linkedin                  
                    ,(
                    SELECT af2.file_url 
                    FROM application_files af2 
                    WHERE af2.application_id = a.id 
                    AND af2.file_type IN ('cv', 'cv_link')
                    ORDER BY af2.created_at DESC 
                    LIMIT 1
                ) as cv             
                ,'Message' as message     
                ,a.application_status as status                  
                ,a.fit_score as fit_score                 
                ,a.notes as notes                 
                ,a.created_at                 
                ,a.updated_at   
                ,ROW_NUMBER() OVER (
                    ORDER BY 
                        CASE WHEN a.fit_score IS NULL THEN 1 ELSE 0 END,
                        a.fit_score DESC NULLS LAST
                ) as rank           
            FROM applications a
            JOIN jobs j ON a.job_id = j.id             
            JOIN users u ON a.candidate_id = u.id             
            WHERE 1=1      
            """
            params = []
            
            if job_id:
                query += " AND a.job_id = %s"
                params.append(job_id)
            
            if statuses:
                placeholders = ', '.join(['%s'] * len(statuses))
                query += f" AND a.application_status IN ({placeholders})"
                params.extend(statuses)
            
            if search:
                query += " AND (u.full_name ILIKE %s OR u.email ILIKE %s)"
                params.extend([f"%{search}%", f"%{search}%"])
            
            # WHITELIST AMAN: Mapping parameter ke nama kolom database
            column_mapping = {
                'created_at': 'a.created_at',
                'fit_score': 'a.fit_score',
                'rank': 'rank',
                # Tambahkan mapping lain jika perlu
            }
            
            # Ambil nama kolom dari mapping, default ke created_at
            order_column = column_mapping.get(sort_by, 'a.created_at')
            
            # Validate sort order
            if sort_order.lower() not in ['asc', 'desc']:
                sort_order = 'desc'
            
            query += f" ORDER BY {order_column} {sort_order} NULLS LAST LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            final_query = cursor.mogrify(query, params)
            logger.info(f"FINAL QUERY => {final_query.decode()}")
            
            cursor.execute(query, params)
            applications = cursor.fetchall()
            
            return applications
            
        except Exception as e:
            logger.error(f"Error getting applications: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)
    
    # def get_application_by_id(self, application_id: int) -> Optional[Dict[str, Any]]:
    #     """Get application by ID"""
    #     try:
    #         conn = get_db_connection()
    #         cursor = conn.cursor()
            
    #         query = """
    #         select 
    #             a.id as id
    #             ,j.id as job_id
    #             ,u.full_name as name
    #             ,j.title as position 
    #             ,a.candidate_education as education 
    #             ,u.phone as phone 
    #             ,u.email as email
    #             ,a.candidate_linkedin as linkedin 
    #             ,a.candidate_cv_url as cv 
    #             ,a.application_status as status 
    #             ,a.fit_score as fit_score
    #             ,a.notes as notes
    #             ,a.created_at
    #             ,a.updated_at 
    #         FROM applications a
    #         JOIN jobs j ON a.job_id = j.id
    #         JOIN users u ON a.candidate_id = u.id
    #         WHERE a.id = %s

    #         """
            
    #         cursor.execute(query, (application_id,))
    #         application = cursor.fetchone()
            
    #         return application
            
    #     except Exception as e:
    #         logger.error(f"Error getting application {application_id}: {e}")
    #         return None

    def get_application_by_id(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed application by ID in user profile format"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Query untuk mendapatkan data user profile dari application
            query = """
            SELECT 
                -- Application fields
                a.id as application_id,
                a.job_id,
                j.title as position,
                a.application_status,
                a.fit_score,
                a.notes,
                a.created_at,
                a.updated_at,
                
                -- User fields (matching user profile structure)
                u.id as user_id,
                u.email,
                u.full_name,
                u.phone,
                u.profile_picture,
                u.linkedin_url,
                'candidate' as role,
                
                -- Candidate info fields
                ci.cv_url,
                ci.cv_extracted_profile,
                ci.cv_extracted_skills,
                ci.cv_extracted_experience,
                ci.cv_extracted_education,
                ci.cv_extracted_certifications,
                ci.cv_extracted_languages,
                ci.preferred_locations,
                ci.preferred_work_modes,
                ci.preferred_job_types,
                ci.expected_salary_min,
                ci.expected_salary_max,
                ci.salary_currency,
                ci.preferred_industries,
                ci.preferred_divisions,
                ci.auto_apply_enabled
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN users u ON a.candidate_id = u.id
            LEFT JOIN candidate_info ci ON u.id = ci.user_id
            WHERE a.id = %s
            """
            
            cursor.execute(query, (application_id,))
            application = cursor.fetchone()
            
            if not application:
                return None
            
            # Extract profile summary
            profile = application.get("cv_extracted_profile")
            summary = None
            location = None
            
            if profile and isinstance(profile, dict):
                summary = profile.get("summary")
                location = profile.get("location")
            
            # Build job preferences
            job_preferences = {
                "preferred_locations": application.get("preferred_locations") or [],
                "preferred_work_modes": application.get("preferred_work_modes") or [],
                "preferred_job_types": application.get("preferred_job_types") or [],
                "expected_salary_min": application.get("expected_salary_min"),
                "expected_salary_max": application.get("expected_salary_max"),
                "salary_currency": application.get("salary_currency"),
                "preferred_industries": application.get("preferred_industries") or [],
                "preferred_divisions": application.get("preferred_divisions") or [],
                "auto_apply_enabled": application.get("auto_apply_enabled") or False,
            }
            
            # Query untuk files
            cursor.execute("""
                SELECT id, file_type, file_url, file_name, created_at
                FROM application_files
                WHERE application_id = %s
                ORDER BY created_at DESC
            """, (application_id,))
            files = cursor.fetchall()
            
            cursor.close()
            
            # Build response matching user profile structure
            response_data = {
                "id": application.get("application_id"),
                "user_id": application.get("user_id"),
                "email": application.get("email"),
                "full_name": application.get("full_name"),
                "phone": application.get("phone"),
                "user_profile": application.get("profile_picture"),
                "linkedin_url": application.get("linkedin_url"),
                "role": application.get("role"),
                "cv_url": application.get("cv_url"),
                "summary": summary,
                "location": location,
                "skills": application.get("cv_extracted_skills") or [],
                "languages": application.get("cv_extracted_languages") or [],
                "experience": application.get("cv_extracted_experience") or [],
                "education": application.get("cv_extracted_education") or [],
                "certifications": application.get("cv_extracted_certifications") or [],
                "job_preferences": job_preferences,
                
                # Application specific fields
                "job_id": application.get("job_id"),
                "position": application.get("position"),
                "application_status": application.get("application_status"),
                "fit_score": application.get("fit_score"),
                "notes": application.get("notes"),
                "created_at": application.get("created_at"),
                "updated_at": application.get("updated_at"),
                "files": [
                    {
                        "id": f.get("id"),
                        "file_type": f.get("file_type"),
                        "file_url": f.get("file_url"),
                        "file_name": f.get("file_name"),
                        "created_at": f.get("created_at"),
                    }
                    for f in files
                ]
                
            }
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error getting application {application_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                    release_connection(conn)
                
        
    
    
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
        

    # async def create_application_with_files(
    #     self,
    #     job_id: int,
    #     coverletter: Optional[str],
    #     portfolio_link: Optional[str],
    #     location: Optional[str],
    #     cv_file: Optional[UploadFile],  # Changed to Optional
    #     cv_link: Optional[str],         # New parameter
    #     portfolio_file: Optional[UploadFile],
    #     candidate_id: int,
    #     actor_role: Optional[str] = None,
    #     actor_ip: Optional[str] = None,
    #     actor_user_agent: Optional[str] = None
    # ) -> Optional[int]:
    #     """Create application with file uploads - commit first approach"""
    #     import traceback
        
    #     conn = None
    #     cursor = None
    #     try:
    #         logger.info(f"Starting application creation for candidate_id: {candidate_id}, job_id: {job_id}")
            
    #         conn = get_db_connection()
    #         cursor = conn.cursor()
            
    #         logger.debug("Database connection acquired")
            
    #         # ===== 1. GET USER DATA =====
    #         cursor.execute(
    #             "SELECT full_name, whatsapp_number FROM users WHERE id = %s", 
    #             (candidate_id,)
    #         )
    #         user_row = cursor.fetchone()
            
    #         logger.debug(f"User data retrieved: {user_row}")
            
    #         if not user_row:
    #             logger.warning(f"User not found: {candidate_id}")
    #             return None
            
    #         # ===== 2. CREATE APPLICATION (COMMIT FIRST) =====
    #         insert_query = """
    #         INSERT INTO applications (
    #             job_id, candidate_id, address, coverletter, portofolio,
    #             application_status, source
    #         ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    #         RETURNING id
    #         """
            
    #         cursor.execute(insert_query, (
    #             job_id,
    #             candidate_id,
    #             location,
    #             coverletter,
    #             portfolio_link,  # Portfolio text/link
    #             'applied',
    #             'website'
    #         ))
            
    #         application_id = cursor.fetchone()['id']
            
    #         # COMMIT NOW - ensure application exists in DB before file upload
    #         conn.commit()
    #         logger.info(f"✅ Application record committed to DB: {application_id}")
            
    #         # ===== 3. HANDLE CV (File or Link) =====
    #         file_service = ApplicationFileService()
            
    #         # CV File Upload
    #         if cv_file and cv_file.filename:
    #             logger.info(f"Uploading CV file: {cv_file.filename}")
    #             try:
    #                 cv_upload_response = await file_service.upload_file(
    #                     application_id=application_id,
    #                     file=cv_file,
    #                     original_filename=cv_file.filename,
    #                     stored_filename=f"cv_{candidate_id}",
    #                     file_type="cv",
    #                     uploader_id=candidate_id,
    #                     uploader_ip=actor_ip,
    #                     uploader_user_agent=actor_user_agent
    #                 )
                    
    #                 if cv_upload_response:
    #                     logger.info(f"✅ CV file uploaded successfully: {cv_upload_response.file_url}")
    #                 else:
    #                     logger.warning("CV file upload returned no response")
    #             except Exception as upload_error:
    #                 logger.error(f"❌ CV file upload failed: {upload_error}")
    #                 # Continue without CV file
            
    #         # CV Link (Save as application_files with type "cv_link")
    #         elif cv_link:
    #             logger.info(f"Saving CV link: {cv_link}")
    #             try:
    #                 # Save CV link to application_files as a special type
    #                 cursor.execute("""
    #                 INSERT INTO application_files (
    #                     application_id, 
    #                     file_name, 
    #                     file_url,
    #                     upload_status,
    #                     file_type,
    #                     created_by,
    #                     uploader_ip,
    #                     uploader_user_agent
    #                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    #                 """, (
    #                     application_id,
    #                     "cv_link",
    #                     cv_link,
    #                     "completed",
    #                     "cv_link",  # Special type for CV links
    #                     candidate_id,
    #                     actor_ip,
    #                     actor_user_agent
    #                 ))
    #                 conn.commit()
    #                 logger.info(f"✅ CV link saved to application_files")
    #             except Exception as link_error:
    #                 logger.error(f"❌ Failed to save CV link: {link_error}")
            
    #         # ===== 4. HANDLE PORTFOLIO FILE =====
    #         if portfolio_file and portfolio_file.filename:
    #             logger.info(f"Uploading portfolio file: {portfolio_file.filename}")
    #             try:
    #                 portfolio_upload_response = await file_service.upload_file(
    #                     application_id=application_id,
    #                     file=portfolio_file,
    #                     original_filename=portfolio_file.filename,
    #                     stored_filename=f"portfolio_{candidate_id}",
    #                     file_type="portfolio",
    #                     uploader_id=candidate_id,
    #                     uploader_ip=actor_ip,
    #                     uploader_user_agent=actor_user_agent
    #                 )
                    
    #                 if portfolio_upload_response:
    #                     logger.info(f"✅ Portfolio file uploaded successfully: {portfolio_upload_response.file_url}")
    #                 else:
    #                     logger.warning("Portfolio file upload returned no response")
    #             except Exception as upload_error:
    #                 logger.error(f"❌ Portfolio file upload failed: {upload_error}")
            
    #         # ===== 5. CREATE APPLICATION HISTORY =====
    #         try:
    #             self._add_application_history(
    #                 application_id, None, None, 'applied',
    #                 None, None, "Application created via form"
    #             )
    #             logger.debug("Application history created")
    #         except Exception as history_error:
    #             logger.error(f"❌ Failed to create application history: {history_error}")
            
    #         # ===== 6. LOG ACTIVITY =====
    #         try:
    #             cursor.execute(
    #                 "SELECT title, created_by FROM jobs WHERE id = %s", 
    #                 (job_id,)
    #             )
    #             job_row = cursor.fetchone()
    #             logger.debug(f"Job data: {job_row}")
    #         except Exception as log_error:
    #             logger.error(f"❌ Failed to log activity: {log_error}")
            
    #         logger.info(f"🎉 Application {application_id} created successfully")
            
    #         return application_id
            
    #     except Exception as e:
    #         logger.error(f"❌ Critical error creating application: {type(e).__name__}: {str(e)}")
    #         logger.error(f"📝 Traceback:\n{traceback.format_exc()}")
            
    #         if conn:
    #             try:
    #                 conn.rollback()
    #                 logger.debug("Transaction rolled back")
    #             except Exception as rollback_error:
    #                 logger.error(f"Rollback failed: {rollback_error}")
            
    #         return None
        
    #     finally:
    #         if cursor:
    #             cursor.close()
    #             logger.debug("Cursor closed")
            
    #         if conn:
    #             try:
    #                 conn.autocommit = True
    #                 release_connection(conn)
    #                 logger.debug("Connection released to pool")
    #             except Exception as release_error:
    #                 logger.error(f"Failed to release connection: {release_error}")

    async def create_application_with_files(
        self,
        job_id: int,
        full_name: str,
        whatsapp_number: str,
        coverletter: Optional[str],
        coverletter_file: Optional[UploadFile],  # New parameter
        portfolio_link: Optional[str],
        location: Optional[str],
        cv_file: Optional[UploadFile],
        cv_link: Optional[str],
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
                application_status, source,
                candidate_name, candidate_wa_number
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            # Use text coverletter even if file is provided (could store summary or different content)
            coverletter_text = coverletter or ""
            
            cursor.execute(insert_query, (
                job_id,
                candidate_id,
                location,
                coverletter_text,  # Use text or placeholder
                portfolio_link,
                'applied',
                'website',
                full_name,
                whatsapp_number
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
                        "cv_link",
                        candidate_id,
                        actor_ip,
                        actor_user_agent
                    ))
                    conn.commit()
                    logger.info(f"✅ CV link saved to application_files")
                except Exception as link_error:
                    logger.error(f"❌ Failed to save CV link: {link_error}")
            
            # ===== 4. HANDLE COVER LETTER FILE =====
            if coverletter_file and coverletter_file.filename:
                logger.info(f"Uploading cover letter file: {coverletter_file.filename}")
                try:
                    coverletter_upload_response = await file_service.upload_file(
                        application_id=application_id,
                        file=coverletter_file,
                        original_filename=coverletter_file.filename,
                        stored_filename=f"coverletter_{candidate_id}",
                        file_type="coverletter",  # New file type
                        uploader_id=candidate_id,
                        uploader_ip=actor_ip,
                        uploader_user_agent=actor_user_agent
                    )
                    
                    if coverletter_upload_response:
                        logger.info(f"✅ Cover letter file uploaded successfully: {coverletter_upload_response.file_url}")
                        
                        # Optional: Update application record to indicate cover letter is in file
                        cursor.execute("""
                        UPDATE applications 
                        SET coverletter = %s 
                        WHERE id = %s
                        """, ("Cover letter provided as file", application_id))
                        conn.commit()
                        
                    else:
                        logger.warning("Cover letter file upload returned no response")
                except Exception as upload_error:
                    logger.error(f"❌ Cover letter file upload failed: {upload_error}")
            
            # ===== 5. HANDLE PORTFOLIO FILE =====
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
            
            # ===== 6. CREATE APPLICATION HISTORY =====
            try:
                self._add_application_history(
                    application_id, None, None, 'applied',
                    None, None, f"Application created via form. Candidate: {full_name}, WhatsApp: {whatsapp_number}"
                )
                logger.debug("Application history created")
            except Exception as history_error:
                logger.error(f"❌ Failed to create application history: {history_error}")
            
            # ===== 7. LOG ACTIVITY =====
            try:
                cursor.execute(
                    "SELECT title, created_by FROM jobs WHERE id = %s", 
                    (job_id,)
                )
                job_row = cursor.fetchone()
                logger.debug(f"Job data: {job_row}")
                
                # Log activity with candidate name
                self._log_activity(
                    user_id=candidate_id,
                    action="submit_application",
                    description=f"Submitted application for job {job_id} as {full_name}",
                    ip_address=actor_ip,
                    user_agent=actor_user_agent
                )
            except Exception as log_error:
                logger.error(f"❌ Failed to log activity: {log_error}")
            
            logger.info(f"🎉 Application {application_id} created successfully for {full_name}")
            
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
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)
    
    def update_application_status_bulk(
        self,
        update_items: List[Dict[str, Any]],
        changed_by: Optional[int] = None,
        actor_role: Optional[str] = None,
        actor_ip: Optional[str] = None,
        actor_user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update multiple application statuses in bulk with individual notes"""
        try:
            if not update_items:
                return {
                    "success": False,
                    "message": "No update items provided",
                    "updated_count": 0,
                    "failed_updates": []
                }
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Validate all statuses first
            cursor.execute("""
                SELECT code 
                FROM master_application_status 
                ORDER BY display_order
            """)
            valid_statuses = [row["code"] for row in cursor.fetchall()]
            invalid_items = []
            
            for item in update_items:
                if item.get("status") not in valid_statuses:
                    invalid_items.append({
                        "application_id": item.get("application_id"),
                        "reason": f"Invalid status: {item.get('status')}. Valid values: {valid_statuses}"
                    })
            
            if invalid_items:
                return {
                    "success": False,
                    "message": "Some items have invalid status",
                    "updated_count": 0,
                    "failed_updates": invalid_items
                }
            
            # Get all application IDs
            application_ids = [item["application_id"] for item in update_items]
            placeholders = ', '.join(['%s'] * len(application_ids))
            
            # Get existing applications
            cursor.execute(f"""
                SELECT id, application_status, job_id, candidate_name, notes
                FROM applications 
                WHERE id IN ({placeholders})
            """, application_ids)
            
            existing_applications = {app["id"]: app for app in cursor.fetchall()}
            
            # Prepare for bulk update
            updated_items = []
            failed_updates = []
            non_existent_ids = []
            
            for item in update_items:
                app_id = item["application_id"]
                new_status = item["status"]
                new_notes = item.get("notes")
                
                if app_id not in existing_applications:
                    non_existent_ids.append(app_id)
                    failed_updates.append({
                        "application_id": app_id,
                        "reason": "Application not found"
                    })
                    continue
                
                # Get current application data
                current_app = existing_applications[app_id]
                
                # Update notes if provided
                final_notes = new_notes if new_notes is not None else current_app.get("notes", "")
                
                try:
                    # Update application
                    update_query = """
                        UPDATE applications 
                        SET application_status = %s, 
                            notes = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        RETURNING id
                    """
                    
                    cursor.execute(update_query, (new_status, final_notes, app_id))
                    result = cursor.fetchone()
                    
                    if result:
                        updated_items.append({
                            "application_id": app_id,
                            "old_status": current_app.get("application_status"),
                            "new_status": new_status,
                            "old_notes": current_app.get("notes", ""),
                            "new_notes": final_notes
                        })
                        
                        # Add to history for each application
                        self._add_application_history(
                            app_id, changed_by,
                            current_app.get("application_status"), new_status,
                            None, None,  # No stage changes
                            f"Status updated. Notes: {final_notes[:100]}" if final_notes else "Status updated"
                        )
                        
                        # Log activity
                        activity_log_service.log_status_update(
                            employer_id=changed_by,
                            job_id=current_app.get("job_id"),
                            applicant_id=app_id,
                            applicant_name=current_app.get("candidate_name"),
                            old_status=current_app.get("application_status"),
                            new_status=new_status,
                            role=actor_role,
                            ip_address=actor_ip,
                            user_agent=actor_user_agent,
                        )
                    else:
                        failed_updates.append({
                            "application_id": app_id,
                            "reason": "Failed to update in database"
                        })
                        
                except Exception as e:
                    logger.error(f"Error updating application {app_id}: {e}")
                    failed_updates.append({
                        "application_id": app_id,
                        "reason": f"Database error: {str(e)}"
                    })
            
            conn.commit()
            cursor.close()
            
            # Prepare response
            success_count = len(updated_items)
            total_count = len(update_items)
            
            if success_count == 0:
                return {
                    "success": False,
                    "message": "Failed to update any applications",
                    "updated_count": 0,
                    "failed_updates": failed_updates,
                    "non_existent_ids": non_existent_ids
                }
            
            return {
                "success": True,
                "message": f"Successfully updated {success_count} of {total_count} application(s)",
                "updated_count": success_count,
                "total_count": total_count,
                "updated_items": updated_items,
                "failed_updates": failed_updates,
                "non_existent_ids": non_existent_ids
            }
            
        except Exception as e:
            logger.error(f"Error in bulk status update: {e}")
            return {
                "success": False,
                "message": f"Internal server error: {str(e)}",
                "updated_count": 0,
                "failed_updates": [{"application_id": item.get("application_id"), "reason": str(e)} 
                                 for item in update_items]
            }
        
        finally:
            if cursor:
                cursor.close()
            if conn:
                    release_connection(conn)
    
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
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

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
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

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
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

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
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def get_active_applications(
        self,
        user_id: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "a.created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict], int]:
        """Get active applications for a candidate with search and pagination"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Active statuses: applied, viewed, qualified, interview (ai_interview + human_interview), contract_proposal
            active_statuses = ['applied', 'viewed', 'qualified', 'ai_interview', 'human_interview', 'contract_proposal']
            status_placeholders = ', '.join(['%s'] * len(active_statuses))
            
            # Build query
            query = f"""
            SELECT
                a.id as id,
                j.id as job_id,
                j.title as title,
                c.name as company_name,
                c.logo_url as company_logo,
                j.location as location,
                COALESCE(a.applied_date, a.created_at) as applied_at,
                a.application_status as status
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            WHERE a.candidate_id = %s
            AND a.application_status IN ({status_placeholders})
            """
            params = [user_id] + active_statuses
            
            # Add status filter if provided
            if status:
                if status == 'interview':
                    query += " AND (a.application_status = 'ai_interview' OR a.application_status = 'human_interview')"
                else:
                    query += " AND a.application_status = %s"
                    params.append(status)
            
            # Add search filter
            if search:
                query += " AND (j.title ILIKE %s OR c.name ILIKE %s)"
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])
            
            # Count total before applying limit
            count_query = f"""
            SELECT COUNT(*) as total
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            WHERE a.candidate_id = %s
            AND a.application_status IN ({status_placeholders})
            """
            count_params = [user_id] + active_statuses
            
            if status:
                if status == 'interview':
                    count_query += " AND (a.application_status = 'ai_interview' OR a.application_status = 'human_interview')"
                else:
                    count_query += " AND a.application_status = %s"
                    count_params.append(status)
            
            if search:
                count_query += " AND (j.title ILIKE %s OR c.name ILIKE %s)"
                search_pattern = f"%{search}%"
                count_params.extend([search_pattern, search_pattern])
            
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()["total"]
            
            # Add sorting
            valid_sort_columns = {'a.created_at', 'a.updated_at', 'applied_at'}
            if sort_by not in valid_sort_columns:
                sort_by = 'a.created_at'
            sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
            query += f" ORDER BY {sort_by} {sort_order} LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert RealDictRow to regular dictionaries
            applications = []
            for row in rows:
                # RealDictRow can be accessed by column name directly
                app_dict = dict(row)
                # Convert integer fields to int
                if 'id' in app_dict and app_dict['id'] is not None:
                    app_dict['id'] = int(app_dict['id'])
                if 'job_id' in app_dict and app_dict['job_id'] is not None:
                    app_dict['job_id'] = int(app_dict['job_id'])
                applications.append(app_dict)
            
            cursor.close()
            
            return applications, total
            
        except Exception as e:
            logger.error(f"Error getting active applications for user {user_id}: {e}")
            return [], 0
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def get_history_applications(
        self,
        user_id: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "a.created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict], int]:
        """Get history applications for a candidate with search and pagination"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # History statuses: not_qualified (as rejected), contract_signed (as hired)
            history_statuses = ['not_qualified', 'contract_signed']
            status_placeholders = ', '.join(['%s'] * len(history_statuses))
            
            # Build query
            query = f"""
            SELECT
                a.id as id,
                j.id as job_id,
                j.title as title,
                c.name as company_name,
                c.logo_url as company_logo,
                a.application_status as status
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            WHERE a.candidate_id = %s
            AND a.application_status IN ({status_placeholders})
            """
            params = [user_id] + history_statuses
            
            # Add status filter if provided
            if status:
                if status in ['not_qualified', 'contract_signed']:
                    query += " AND a.application_status = %s"
                    params.append(status)
                else:
                    query += " AND a.application_status = %s"
                    params.append(status)
            
            # Add search filter
            if search:
                query += " AND (j.title ILIKE %s OR c.name ILIKE %s)"
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])
            
            # Count total before applying limit
            count_query = f"""
            SELECT COUNT(*) as total
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            WHERE a.candidate_id = %s
            AND a.application_status IN ({status_placeholders})
            """
            count_params = [user_id] + history_statuses
            
            if status:
                if status in ['not_qualified', 'contract_signed']:
                    count_query += " AND a.application_status = %s"
                    count_params.append(status)
                else:
                    count_query += " AND a.application_status = %s"
                    count_params.append(status)
            
            if search:
                count_query += " AND (j.title ILIKE %s OR c.name ILIKE %s)"
                search_pattern = f"%{search}%"
                count_params.extend([search_pattern, search_pattern])
            
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()["total"]
            
            # Add sorting
            valid_sort_columns = {'a.created_at', 'a.updated_at'}
            if sort_by not in valid_sort_columns:
                sort_by = 'a.created_at'
            sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
            query += f" ORDER BY {sort_by} {sort_order} LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert RealDictRow to regular dictionaries
            applications = []
            for row in rows:
                # RealDictRow can be accessed by column name directly
                app_dict = dict(row)
                # Convert integer fields to int
                if 'id' in app_dict and app_dict['id'] is not None:
                    app_dict['id'] = int(app_dict['id'])
                if 'job_id' in app_dict and app_dict['job_id'] is not None:
                    app_dict['job_id'] = int(app_dict['job_id'])
                applications.append(app_dict)
            
            cursor.close()
            
            return applications, total
            
        except Exception as e:
            logger.error(f"Error getting history applications for user {user_id}: {e}")
            return [], 0
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

