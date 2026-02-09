
from loguru import logger
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.services.database import get_db_connection, release_connection
from app.schemas.job import JobCreate, JobStatus


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
        search: Optional[str] = None,
        is_bookmark: Optional[bool] = None,
        user_id: Optional[int] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        company_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get list of jobs with optional filters"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Build SELECT clause
            query = """
                SELECT 
                    j.*,
                    c.id as company_id,
                    c.name as company_name,
                    c.description as company_description,
                    c.logo_url as company_logo_url,
                    c.banner_url as company_banner_url,
                    cu.last_active_at as last_recruiter_active_at,
                    COALESCE(v.view_count, 0) as count_views,
                    COALESCE(a.app_count, 0) as count_applications
            """
            
            # Tambahkan field is_bookmark jika user_id diberikan
            if user_id is not None:
                query += """,
                    EXISTS (
                        SELECT 1 FROM job_bookmarks jb 
                        WHERE jb.job_id = j.id AND jb.user_id = %s
                    ) as is_bookmark
                """
            
            # Build FROM clause dengan subqueries untuk count
            query += """
                FROM jobs j
                LEFT JOIN companies c ON j.company_id = c.id
                LEFT JOIN users cu ON j.created_by = cu.id
                LEFT JOIN (
                    SELECT job_id, COUNT(*) as view_count
                    FROM job_views
                    GROUP BY job_id
                ) v ON v.job_id = j.id
                LEFT JOIN (
                    SELECT job_id, COUNT(*) as app_count
                    FROM applications
                    GROUP BY job_id
                ) a ON a.job_id = j.id
                WHERE 1=1
            """
            
            params = []
            
            # Tambahkan user_id parameter untuk EXISTS jika ada
            if user_id is not None:
                params.append(user_id)
            
            # Tambahkan JOIN untuk filter bookmark jika diperlukan
            if is_bookmark is not None and user_id is not None:
                if is_bookmark:
                    query += " AND EXISTS (SELECT 1 FROM job_bookmarks jb WHERE jb.job_id = j.id AND jb.user_id = %s)"
                    params.append(user_id)
                else:
                    query += " AND NOT EXISTS (SELECT 1 FROM job_bookmarks jb WHERE jb.job_id = j.id AND jb.user_id = %s)"
                    params.append(user_id)
            
            # HANYA filter status jika diberikan
            if status:
                query += " AND j.status = %s"
                params.append(status)

            if department:
                query += " AND j.department = %s"
                params.append(department)

            if employment_type:
                query += " AND j.employment_type ILIKE %s"
                params.append(employment_type)

            if location:
                query += " AND j.location ILIKE %s"
                params.append(f"%{location}%")

            if working_type:
                query += " AND j.working_type ILIKE %s"
                params.append(working_type)

            if search:
                search_term = f"%{search}%"
                query += """
                    AND (
                        j.title ILIKE %s 
                        OR j.description ILIKE %s
                        OR c.name ILIKE %s
                        OR j.location ILIKE %s
                        OR j.department ILIKE %s
                    )
                """
                params.extend([search_term, search_term, search_term, search_term, search_term])

            if salary_min is not None:
                query += " AND j.salary_min >= %s"
                params.append(salary_min)
                
            if salary_max is not None:
                query += " AND j.salary_max <= %s"
                params.append(salary_max)

            if company_id is not None:
                query += " AND j.company_id = %s"
                params.append(company_id)

            query += " ORDER BY j.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            jobs = cursor.fetchall()
            
            # Format response dengan struktur company
            formatted_jobs = []
            for job in jobs:
                job_dict = dict(job)
                
                # Pastikan is_bookmark ada dalam response jika user_id diberikan
                if user_id is not None and 'is_bookmark' not in job_dict:
                    job_dict['is_bookmark'] = False
                
                # Pastikan count_views dan count_applications ada
                if 'count_views' not in job_dict:
                    job_dict['count_views'] = 0
                if 'count_applications' not in job_dict:
                    job_dict['count_applications'] = 0
                
                # Buat struktur company jika ada company_id
                if job_dict.get('company_id'):
                    job_dict['company'] = {
                        'id': job_dict['company_id'],
                        'name': job_dict.get('company_name', ''),
                        'description': job_dict.get('company_description', ''),
                        'logo_url': job_dict.get('company_logo_url', ''),
                        'banner_url': job_dict.get('company_banner_url', '')
                    }
                    # Hapus field yang tidak diperlukan
                    job_dict.pop('company_name', None)
                else:
                    job_dict['company'] = None
                    
                formatted_jobs.append(job_dict)
                
            return formatted_jobs

        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)


    def get_jobs_count(
        self,
        status: Optional[str] = None,
        department: Optional[str] = None,
        employment_type: Optional[str] = None,
        location: Optional[str] = None,
        working_type: Optional[str] = None,
        search: Optional[str] = None,
        is_bookmark: Optional[bool] = None,
        user_id: Optional[int] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        company_id: Optional[int] = None,
    ) -> int:
        """Get total count of jobs with optional filters"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Count query dengan subqueries untuk menghindari pengaruh LEFT JOIN
            count_query = """
                SELECT COUNT(DISTINCT j.id) as total 
                FROM jobs j
                LEFT JOIN companies c ON j.company_id = c.id
                WHERE 1=1
            """
            params = []
            
            # Filter bookmark dengan EXISTS
            if is_bookmark is not None and user_id is not None:
                if is_bookmark:
                    count_query += " AND EXISTS (SELECT 1 FROM job_bookmarks jb WHERE jb.job_id = j.id AND jb.user_id = %s)"
                    params.append(user_id)
                else:
                    count_query += " AND NOT EXISTS (SELECT 1 FROM job_bookmarks jb WHERE jb.job_id = j.id AND jb.user_id = %s)"
                    params.append(user_id)
            
            # HANYA filter status jika diberikan
            if status:
                count_query += " AND j.status = %s"
                params.append(status)

            if department:
                count_query += " AND j.department = %s"
                params.append(department)

            if employment_type:
                count_query += " AND j.employment_type ILIKE %s"
                params.append(employment_type)

            if location:
                count_query += " AND j.location ILIKE %s"
                params.append(f"%{location}%")

            if working_type:
                count_query += " AND j.working_type ILIKE %s"
                params.append(working_type)

            if search:
                search_term = f"%{search}%"
                count_query += """
                    AND (
                        j.title ILIKE %s 
                        OR j.description ILIKE %s
                        OR c.name ILIKE %s
                        OR j.location ILIKE %s
                        OR j.department ILIKE %s
                    )
                """
                params.extend([search_term, search_term, search_term, search_term, search_term])

            if salary_min is not None:
                count_query += " AND j.salary_min >= %s"
                params.append(salary_min)
            
            if salary_max is not None:
                count_query += " AND j.salary_max <= %s"
                params.append(salary_max)

            if company_id is not None:
                count_query += " AND j.company_id = %s"
                params.append(company_id)

            cursor.execute(count_query, params)
            result = cursor.fetchone()
            return result["total"] if result else 0
                
        except Exception as e:
            logger.error(f"Error counting jobs: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)


    def get_job_by_id(self, job_id: int, user_id: Optional[int] = None, 
                    user_agent: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get job by ID with optional bookmark status for user and similar jobs"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query utama untuk mendapatkan job detail
            query = """
                SELECT 
                    j.*,
                    c.id as company_id,
                    c.name as company_name,
                    c.description as company_description,
                    c.logo_url as company_logo_url,
                    c.banner_url as company_banner_url,
                    cu.last_active_at as last_recruiter_active_at,
                    COALESCE(v.view_count, 0) as count_views,
                    COALESCE(a.app_count, 0) as count_applications
            """
            
            # Tambahkan field is_bookmark jika user_id diberikan
            if user_id is not None:
                query += """,
                    EXISTS (
                        SELECT 1 FROM job_bookmarks jb 
                        WHERE jb.job_id = j.id AND jb.user_id = %s
                    ) as is_bookmark
                """
            
            query += """
                FROM jobs j
                LEFT JOIN companies c ON j.company_id = c.id
                LEFT JOIN users cu ON j.created_by = cu.id
                LEFT JOIN (
                    SELECT job_id, COUNT(*) as view_count
                    FROM job_views
                    GROUP BY job_id
                ) v ON v.job_id = j.id
                LEFT JOIN (
                    SELECT job_id, COUNT(*) as app_count
                    FROM applications
                    GROUP BY job_id
                ) a ON a.job_id = j.id
                WHERE j.id = %s
            """
            
            # Parameter: user_id (jika ada) dulu, baru job_id
            params = [user_id] if user_id is not None else []
            params.append(job_id)
            
            cursor.execute(query, tuple(params))
            job = cursor.fetchone()

            if not job:
                return None
                
            # Konversi ke dictionary
            job_dict = dict(job)
            
            # Pastikan is_bookmark ada dalam response jika user_id diberikan
            if user_id is not None and 'is_bookmark' not in job_dict:
                job_dict['is_bookmark'] = False
            
            # Pastikan count_views dan count_applications ada
            if 'count_views' not in job_dict:
                job_dict['count_views'] = 0
            if 'count_applications' not in job_dict:
                job_dict['count_applications'] = 0
            
            # Buat struktur company jika ada company_id
            if job_dict.get('company_id'):
                job_dict['company'] = {
                    'id': job_dict['company_id'],
                    'name': job_dict.get('company_name', ''),
                    'description': job_dict.get('company_description', ''),
                    'logo_url': job_dict.get('company_logo_url', ''),
                    'banner_url': job_dict.get('company_banner_url', '')
                }
                # Hapus field yang tidak diperlukan
                job_dict.pop('company_name', None)
                job_dict.pop('company_description', None)
            else:
                job_dict['company'] = None
            
            # Get similar jobs (always include) dengan user_id untuk bookmark status
            similar_jobs = self.get_similar_jobs(job_dict, user_id=user_id, limit=5)
            job_dict['similar_jobs'] = similar_jobs
            
            # RECORD JOB VIEW (Setelah mendapatkan data job)
            self.record_job_view(
                job_id=job_id,
                user_id=user_id,
                user_agent=user_agent
            )
                
            return job_dict

        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)


    def get_similar_jobs(self, current_job: Dict[str, Any], user_id: Optional[int] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar jobs based on current job's attributes"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            job_id = current_job.get('id')
            department = current_job.get('department')
            employment_type = current_job.get('employment_type')
            experience_level = current_job.get('experience_level')
            location = current_job.get('location')
            working_type = current_job.get('working_type')
            
            # Build query untuk similar jobs dengan semua field yang diperlukan
            query = """
                SELECT 
                    j.id,
                    j.title,
                    j.experience_level,
                    j.salary_min,
                    j.salary_max,
                    j.description,
                    j.employment_type,
                    j.working_type,
                    j.is_scam,
                    c.name as company_name,
                    c.logo_url as company_logo_url,
                    c.banner_url as company_banner_url,
                    us.last_active_at as last_recruiter_active_at
            """
            
            # Tambahkan is_bookmark jika user_id diberikan
            if user_id is not None:
                query += """,
                    EXISTS (
                        SELECT 1 FROM job_bookmarks jb 
                        WHERE jb.job_id = j.id AND jb.user_id = %s
                    ) as is_bookmark
                """
                # Parameter pertama adalah user_id untuk bookmark
                params = [user_id, job_id]
            else:
                params = [job_id]
            
            query += """
                FROM jobs j
                LEFT JOIN companies c ON j.company_id = c.id
                LEFT JOIN users us on j.created_by = us.id
                WHERE j.id != %s
                AND j.status = 'published'
            """
            
            # Perhatikan: job_id sudah ada di params[0] atau params[1] tergantung user_id
            
            # Prioritaskan berdasarkan kesamaan (bisa disesuaikan)
            conditions = []
            
            # 1. Same department (highest priority)
            if department:
                conditions.append("(j.department = %s)")
                params.append(department)
            
            # 2. Same employment type
            if employment_type:
                conditions.append("(j.employment_type = %s)")
                params.append(employment_type)
            
            # 3. Same working type
            if working_type:
                conditions.append("(j.working_type = %s)")
                params.append(working_type)
            
            # 4. Similar experience level
            if experience_level:
                conditions.append("(j.experience_level = %s)")
                params.append(experience_level)
            
            # 5. Same location
            if location:
                conditions.append("(j.location ILIKE %s)")
                params.append(f"%{location}%")
            
            # Jika ada kondisi, tambahkan ke query
            if conditions:
                query += " AND (" + " OR ".join(conditions) + ")"
            else:
                # Jika tidak ada kondisi yang bisa digunakan, cari berdasarkan job category/industry
                query += " AND j.department IS NOT NULL"
            
            # Order by: prioritize same department, then employment type, then working type
            order_conditions = []
            if department:
                order_conditions.append("CASE WHEN j.department = %s THEN 1 ELSE 0 END DESC")
                params.append(department)
            if employment_type:
                order_conditions.append("CASE WHEN j.employment_type = %s THEN 1 ELSE 0 END DESC")
                params.append(employment_type)
            if working_type:
                order_conditions.append("CASE WHEN j.working_type = %s THEN 1 ELSE 0 END DESC")
                params.append(working_type)
            if experience_level:
                order_conditions.append("CASE WHEN j.experience_level = %s THEN 1 ELSE 0 END DESC")
                params.append(experience_level)
            
            if order_conditions:
                query += " ORDER BY " + ", ".join(order_conditions)
            
            # Default order by created_at jika tidak ada kondisi
            query += ", j.created_at DESC"
            
            query += " LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, tuple(params))
            similar_jobs = cursor.fetchall()
            
            # Format hasil
            formatted_similar_jobs = []
            for job in similar_jobs:
                job_dict = dict(job)
                
                # Truncate description jika terlalu panjang
                description = job_dict.get('description', '')
                if description and len(description) > 150:
                    job_dict['description'] = description[:150] + '...'
                
                # Pastikan semua field ada dengan nilai default
                if 'experience_level' not in job_dict:
                    job_dict['experience_level'] = None
                if 'salary_min' not in job_dict:
                    job_dict['salary_min'] = None
                if 'salary_max' not in job_dict:
                    job_dict['salary_max'] = None
                if 'employment_type' not in job_dict:
                    job_dict['employment_type'] = None
                if 'working_type' not in job_dict:
                    job_dict['working_type'] = None
                if 'is_scam' not in job_dict:
                    job_dict['is_scam'] = False
                if 'company_name' not in job_dict or job_dict['company_name'] is None:
                    job_dict['company_name'] = None
                
                # Jika tidak ada user_id, set is_bookmark ke False
                if user_id is None and 'is_bookmark' not in job_dict:
                    job_dict['is_bookmark'] = False
                # Jika ada user_id tapi field is_bookmark tidak ada (seharusnya tidak terjadi)
                elif user_id is not None and 'is_bookmark' not in job_dict:
                    job_dict['is_bookmark'] = False
                
                formatted_similar_jobs.append(job_dict)
            
            return formatted_similar_jobs
            
        except Exception as e:
            logger.error(f"Error getting similar jobs: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    def record_job_view(self, job_id: int, user_id: Optional[int] = None,
                        user_agent: Optional[str] = None) -> bool:
        """Record a job view in the database"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Insert view record - SESUAI INSTRUKSI
            query = """
                INSERT INTO job_views (job_id, user_id, viewed_at, user_agent)
                VALUES (%s, %s, CURRENT_TIMESTAMP, %s)
            """
            params = (job_id, user_id, user_agent)
            
            cursor.execute(query, params)
            conn.commit()
            
            logger.debug(f"Recorded view for job {job_id}, user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording job view: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    

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
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

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
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

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
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

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
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

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
                    "error": "Internal server error"
                }
            
            return job
            
        except Exception as e:
            logger.error(f"Error getting job with scoring {job_id}: {str(e)}")
            raise
    
    def get_public_jobs(
        self,
        employment_type: Optional[str] = None,
        working_type: Optional[str] = None,
        search_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get public jobs for landing page.
        - Only 'published' jobs.
        - Limit 10, newest first.
        - Joins with company data.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1. Build Query
            query = """
                SELECT 
                    j.id, j.title, j.location, j.employment_type, j.working_type,
                    j.salary_min, j.salary_max, j.salary_currency, j.salary_interval,
                    j.created_at, j.department, j.experience_level, j.description,
                    c.name as company_name, c.logo_url as company_logo
                FROM jobs j
                LEFT JOIN companies c ON j.company_id = c.id
                WHERE j.status IN ('published', 'open')
            """
            params = []

            if employment_type:
                query += " AND j.employment_type = %s"
                params.append(employment_type)

            if working_type:
                query += " AND j.working_type = %s"
                params.append(working_type)

            if search_title:
                query += " AND j.title ILIKE %s"
                params.append(f"%{search_title}%")

            # Store the current data query
            data_query = query + " ORDER BY j.created_at DESC LIMIT 10"

            # 2. Get Data
            cursor.execute(data_query, tuple(params))
            rows = cursor.fetchall()

            # 3. Get Total (for landing page info)
            # Use the base query but wrap it in COUNT - avoid f-string for query
            count_query = "SELECT COUNT(*) as total FROM (" + query + ") AS base"
            cursor.execute(count_query, tuple(params))
            count_row = cursor.fetchone()
            total = count_row['total'] if hasattr(count_row, 'keys') else count_row[0]

            # 4. Format Results
            jobs = []
            for row in rows:
                is_dict = hasattr(row, 'keys')
                
                # Extract salary as float if not None
                s_min = row['salary_min'] if is_dict else row[5]
                s_max = row['salary_max'] if is_dict else row[6]
                
                # Extract base fields
                job_data = {
                    'id': row['id'] if is_dict else row[0],
                    'title': row['title'] if is_dict else row[1],
                    'department': row['department'] if is_dict else row[10],
                    'location': row['location'] if is_dict else row[2],
                    'employment_type': row['employment_type'] if is_dict else row[3],
                    'working_type': row['working_type'] if is_dict else row[4],
                    'experience_level': row['experience_level'] if is_dict else row[11],
                    'description': row['description'] if is_dict else row[12],
                    'salary_min': float(s_min) if s_min is not None else None,
                    'salary_max': float(s_max) if s_max is not None else None,
                    'salary_currency': row['salary_currency'] if is_dict else row[7],
                    'salary_interval': row['salary_interval'] if is_dict else row[8],
                    'created_at': row['created_at'] if is_dict else row[9],
                    'company_name': row['company_name'] if is_dict else row[13],
                    'company_logo': row['company_logo'] if is_dict else row[14],
                }
                
                jobs.append(job_data)

            return {
                "total": total,
                "jobs": jobs
            }

        except Exception as e:
            logger.error(f"Error fetching public jobs: {e}")
            return {"total": 0, "jobs": []}
        finally:
            if cursor: cursor.close()
            release_connection(conn)
    
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

    def get_job_recommendations(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get job recommendations dengan pagination
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 1. Get published jobs dengan pagination
            query = """
                SELECT 
                    j.id,
                    j.title,
                    j.location,
                    j.employment_type,
                    j.working_type,
                    j.experience_level,
                    j.salary_min,
                    j.salary_max,
                    j.salary_currency,
                    j.salary_interval,
                    j.created_at,
                    c.name as company_name,
                    c.logo_url as company_logo
                FROM jobs j
                LEFT JOIN companies c ON j.company_id = c.id
                WHERE j.status IN ('published', 'open')
                AND j.id NOT IN (
                    SELECT DISTINCT job_id 
                    FROM applications 
                    WHERE candidate_id = %s
                )
                ORDER BY j.created_at DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, (user_id, limit, offset))
            jobs = cursor.fetchall()
            
            # 2. Get user's bookmarks
            cursor.execute(
                "SELECT job_id FROM job_bookmarks WHERE user_id = %s",
                (user_id,)
            )
            bookmarks = {row['job_id'] for row in cursor.fetchall()}
            
            # 3. Format jobs dengan match score
            recommendations = []
            for job in jobs:
                job_id = int(job['id'])
                
                # Simple match score calculation
                match_score = self._calculate_simple_match_score(job)
                
                # Check if bookmarked
                is_bookmarked = job_id in bookmarks
                
                # Format the job
                job_dict = {
                    'id': job_id,
                    'title': job['title'],
                    'company_name': job['company_name'],
                    'company_logo': job['company_logo'],
                    'location': job['location'],
                    'employment_type': job['employment_type'],
                    'working_type': job['working_type'],
                    'experience_level': job['experience_level'],
                    'salary_min': float(job['salary_min']) if job['salary_min'] else None,
                    'salary_max': float(job['salary_max']) if job['salary_max'] else None,
                    'salary_currency': job['salary_currency'] or 'IDR',
                    'salary_interval': job['salary_interval'] or 'monthly',
                    'match_score': round(match_score, 2),
                    'match_reasons': self._get_match_reasons(job, match_score),
                    'is_bookmarked': is_bookmarked,
                    'created_at': job['created_at']
                }
                
                recommendations.append(job_dict)
            
            # Sort by match score
            recommendations.sort(key=lambda x: x['match_score'], reverse=True)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in get_job_recommendations: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    def get_job_recommendations_count(self, user_id: int) -> int:
        """
        Get total count of job recommendations untuk user
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT COUNT(*) as total
                FROM jobs j
                WHERE j.status IN ('published', 'open')
                AND j.id NOT IN (
                    SELECT DISTINCT job_id 
                    FROM applications 
                    WHERE candidate_id = %s
                )
            """
            
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            return result['total'] if result else 0
            
        except Exception as e:
            logger.error(f"Error in get_job_recommendations_count: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)
    
    def _calculate_simple_match_score(self, job: Dict) -> float:
        """Simple match score calculation"""
        score = 50.0  # Base score
        
        # Bonus for complete information
        if job.get('salary_min') and job.get('salary_max'):
            score += 10
        
        if job.get('company_name'):
            score += 5
        
        if job.get('experience_level'):
            score += 5
        
        if job.get('working_type') == 'remote':
            score += 10
        
        # Ensure max 100
        return min(score, 100.0)
    
    def _get_match_reasons(self, job: Dict, score: float) -> List[str]:
        """Get simple match reasons"""
        reasons = []
        
        if score >= 70:
            reasons.append("Highly recommended")
        elif score >= 50:
            reasons.append("Good match")
        else:
            reasons.append("Based on your profile")
        
        if job.get('working_type') == 'remote':
            reasons.append("Remote work available")
        
        if job.get('salary_min') and job.get('salary_max'):
            reasons.append("Salary information provided")
        
        return reasons
    
    def get_user_application_insights(self, user_id: int) -> Dict[str, Any]:
        """Get simple application insights for user"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Count applications
            cursor.execute(
                "SELECT COUNT(*) as total FROM applications WHERE candidate_id = %s",
                (user_id,)
            )
            total_apps = cursor.fetchone()['total']
            
            # Count by status
            cursor.execute("""
                SELECT application_status, COUNT(*) as count 
                FROM applications 
                WHERE candidate_id = %s 
                GROUP BY application_status
            """, (user_id,))
            
            status_counts = {}
            for row in cursor.fetchall():
                status_counts[row['application_status']] = row['count']
            
            return {
                'total_applications': total_apps,
                'status_counts': status_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting application insights: {e}")
            return {'total_applications': 0, 'status_counts': {}}
        finally:
            if cursor:
                cursor.close()
            release_connection(conn)

    async def generate_ai_description(self, job_data: dict) -> dict:
        """
        Simple AI generation with Ollama
        """
        try:
            # Call Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "mistral",
                    "prompt": f"Buat deskripsi pekerjaan {job_data.get('title')} dalam bahasa Indonesia",
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                ai_text = response.json()["response"]
                return {
                    "description": ai_text,
                    "requirements": "Generated by AI",
                    "responsibilities": "Generated by AI", 
                    "benefits": "Generated by AI"
                }
            else:
                return {}
                
        except:
            return {}