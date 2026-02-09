import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.schemas.user import UserResponse
from app.services.database import get_db_connection, release_connection


class DashboardService:
    """
    Service untuk mendapatkan data dashboard employer.
    """

    def __init__(self):
        pass

    def get_profile(self, current_user: UserResponse) -> Dict[str, Any]:
        """
        Get profile data from current_user.
        Returns: {"id": int, "name": str}
        """
        try:
            return {
                "id": current_user.id,
                "name": current_user.full_name
            }
        except Exception as exc:
            logger.error(f"Failed to get profile from current_user: {exc}")
            return None

    def get_team_members(self, current_user: UserResponse) -> Optional[List[Dict[str, Any]]]:
        """
        Get team members data.
        Returns: list of team members
        """
        cursor = None
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Gunakan company_id dari current_user
            company_id = current_user.company_id
            
            if not company_id:
                logger.warning(f"No company_id found for user {current_user.id}")
                return None
            
            cursor.execute(
                """
                SELECT 
                    u.id,
                    COALESCE(u.full_name, u.username) AS name,
                    r.name AS role,
                    COALESCE(u.profile_picture, '') AS profile_picture
                FROM users u
                INNER JOIN users_companies uc ON u.id = uc.user_id
                INNER JOIN user_roles ur ON u.id = ur.user_id
                INNER JOIN roles r ON ur.role_id = r.id
                WHERE uc.company_id = %s
                ORDER BY u.id
                """,
                (company_id,)
            )
            results = cursor.fetchall()

            if not results:
                logger.info(f"No team members found for company_id {company_id}")
                return None

            # Transform results
            team_members = []
            for row in results:
                # Jika profile_picture kosong, gunakan default
                profile_pic = row["profile_picture"]
                if not profile_pic:
                    profile_pic = "https://i.pravatar.cc/150"
                
                team_members.append({
                    "id": row["id"],
                    "name": row["name"],
                    "role": row["role"].lower() if row["role"] else "recruiter",
                    "profile_picture": profile_pic
                })

            return team_members
            
        except Exception as exc:
            logger.error(f"Failed to get team members for user {current_user.id}: {exc}")
            return None
        finally:
            # PASTIKAN selalu close connection
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def get_company_profile(self, current_user: UserResponse) -> Optional[Dict[str, Any]]:
        """
        Get company profile data.
        Returns: company profile information
        """
        cursor = None
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Gunakan company_id dari current_user
            company_id = current_user.company_id
            
            if not company_id:
                logger.warning(f"No company_id found for user {current_user.id}")
                return None
            
            cursor.execute(
                """
                SELECT 
                    id,
                    name,
                    industry,
                    logo_url,
                    banner_url as cover_image_url
                FROM companies
                WHERE id = %s
                """,
                (company_id,)
            )
            result = cursor.fetchone()

            if not result:
                logger.warning(f"No company found for company_id {company_id}")
                return None

            # Generate default logo URL jika logo_url kosong atau NULL
            logo_url = result["logo_url"]
            if not logo_url and result["name"]:
                # Generate avatar dari nama perusahaan
                company_name = result["name"].replace(' ', '+')
                logo_url = f"https://ui-avatars.com/api/?name={company_name}"
            
            return {
                "id": result["id"],
                "name": result["name"] or "Perusahaan",
                "industry": result["industry"] or "Industri",
                "logo_url": logo_url or "https://ui-avatars.com/api/?name=Company",
                "cover_image_url": result["cover_image_url"] or "https://picsum.photos/1200/400"
            }
            
        except Exception as exc:
            logger.error(f"Failed to get company profile for user {current_user.id}: {exc}")
            return None
        finally:
            # PASTIKAN selalu close connection
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def get_jobs_summary(self, current_user: UserResponse) -> Optional[Dict[str, Any]]:
        """
        Get jobs summary data.
        Returns: jobs summary including active jobs, applications, trend, etc.
        """
        cursor = None
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Gunakan company_id dari current_user
            company_id = current_user.company_id
            
            if not company_id:
                logger.warning(f"No company_id found for user {current_user.id}")
                return None
            
            # 1. Active jobs count
            cursor.execute(
                """
                SELECT COUNT(*) as active_jobs
                FROM jobs 
                WHERE company_id = %s 
                AND status = 'published'
                """,
                (company_id,)
            )
            active_jobs_result = cursor.fetchone()
            active_jobs = active_jobs_result["active_jobs"] if active_jobs_result else 0

            # 2. Total applications
            cursor.execute(
                """
                SELECT COUNT(DISTINCT a.id) as total_applications
                FROM applications a
                INNER JOIN jobs j ON a.job_id = j.id
                WHERE j.company_id = %s
                """,
                (company_id,)
            )
            total_applications_result = cursor.fetchone()
            total_applications = total_applications_result["total_applications"] if total_applications_result else 0

            # 3. New applications (7 hari terakhir)
            cursor.execute(
                """
                SELECT COUNT(DISTINCT a.id) as new_applications
                FROM applications a
                INNER JOIN jobs j ON a.job_id = j.id
                WHERE j.company_id = %s
                AND a.created_at >= NOW() - INTERVAL '7 days'
                """,
                (company_id,)
            )
            new_applications_result = cursor.fetchone()
            new_applications = new_applications_result["new_applications"] if new_applications_result else 0

            # 4. New jobs (30 hari terakhir)
            cursor.execute(
                """
                SELECT COUNT(*) as new_jobs
                FROM jobs
                WHERE company_id = %s
                AND created_at >= NOW() - INTERVAL '30 days'
                """,
                (company_id,)
            )
            new_jobs_result = cursor.fetchone()
            new_jobs = new_jobs_result["new_jobs"] if new_jobs_result else 0

            # 5. Most applied jobs (null for now)
            cursor.execute(
                """
                SELECT 
                    j.id as job_id,
                    j.title,
                    COUNT(a.id) as total_applicants,
                    100 as max_applicants
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id
                WHERE j.company_id = %s
                GROUP BY j.id, j.title
                ORDER BY COUNT(a.id) DESC
                LIMIT 5
                """,
                (company_id,)
            )
            most_applied_results = cursor.fetchall()
            
            most_applied_jobs = []
            for row in most_applied_results:
                most_applied_jobs.append({
                    "job_id": row["job_id"],
                    "title": row["title"] or f"Job {row['job_id']}",
                    "total_applicants": row["total_applicants"] or 0,
                    "max_applicants": row["max_applicants"] or 100
                })
            
            # 6. Jobs trend (null for now)
            current_year = datetime.now().year
            cursor.execute(
                """
                SELECT 
                    TO_CHAR(created_at, 'Mon') as month_short,
                    EXTRACT(MONTH FROM created_at) as month_num,
                    COUNT(*) as total_jobs
                FROM jobs
                WHERE company_id = %s
                AND EXTRACT(YEAR FROM created_at) = %s
                GROUP BY TO_CHAR(created_at, 'Mon'), EXTRACT(MONTH FROM created_at)
                ORDER BY EXTRACT(MONTH FROM created_at)
                """,
                (company_id, current_year)
            )
            trend_results = cursor.fetchall()

            # Map month names (English short)
            month_map = {
                'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Apr',
                'May': 'May', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Aug',
                'Sep': 'Sep', 'Oct': 'Oct', 'Nov': 'Nov', 'Dec': 'Dec'
            }

            # Buat dictionary dari hasil query untuk lookup mudah
            trend_dict = {}
            for row in trend_results:
                month_name = month_map.get(row["month_short"], row["month_short"])
                trend_dict[row["month_num"]] = {
                    "month": month_name,
                    "total_jobs": row["total_jobs"]
                }

            # Generate 12 bulan dengan default 0 untuk bulan yang tidak ada data
            jobs_trend_data = []
            for month_num in range(1, 13):  # 1 sampai 12
                if month_num in trend_dict:
                    # Jika ada data dari query
                    jobs_trend_data.append(trend_dict[month_num])
                else:
                    # Jika tidak ada data, buat dengan total_jobs = 0
                    # Cari nama bulan dari month_num
                    month_names = [
                        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
                    ]
                    month_name = month_names[month_num - 1] if month_num <= 12 else f"M{month_num}"
                    
                    jobs_trend_data.append({
                        "month": month_name,
                        "total_jobs": 0
                    })

            jobs_trend = {
                "year": current_year,
                "unit": "month",
                "data": jobs_trend_data
            }

            return {
                "active_jobs": active_jobs,
                "total_applications": total_applications,
                "new_applications": new_applications,
                "new_jobs": new_jobs,
                "most_applied_jobs": most_applied_jobs,
                "jobs_trend": jobs_trend
            }
            
        except Exception as exc:
            logger.error(f"Failed to get jobs summary for user {current_user.id}: {exc}")
            return None
        finally:
            # PASTIKAN selalu close connection
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def get_dashboard_data(self, current_user: UserResponse) -> Dict[str, Any]:
        """
        Get complete dashboard data.
        Main method to call all dashboard components.
        """
        try:
            # 1. Get profile data
            profile = self.get_profile(current_user)
            
            # 2. Get team members (null for now)
            team_members = self.get_team_members(current_user)
            
            # 3. Get company profile (null for now)
            company_profile = self.get_company_profile(current_user)
            
            # 4. Get jobs summary (null for now)
            jobs_summary = self.get_jobs_summary(current_user)

            return {
                "profile": profile,
                "team_members": team_members,
                "company_profile": company_profile,
                "jobs_summary": jobs_summary
            }
            
        except Exception as exc:
            logger.error(f"Failed to get dashboard data: {exc}")
            raise


# Create singleton instance
dashboard_service = DashboardService()