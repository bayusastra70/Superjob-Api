# import logging
# from typing import List, Dict, Any, Optional
# from datetime import datetime

# from app.core.config import settings
# from app.schemas.candidate import CandidateScoreCreate
# from app.services.database import get_db_connection  # ← UPDATE IMPORT

# logger = logging.getLogger(__name__)

# class CandidateService:
#     def __init__(self):
#         pass

#     def create_candidate_score_table(self):
#         """Create candidate_score table - using standalone database"""
#         try:
#             conn = get_db_connection()  # ← Use standalone connection
#             cursor = conn.cursor()

#             create_table_query = """
#             CREATE TABLE IF NOT EXISTS candidate_score (
#                 id SERIAL PRIMARY KEY,
#                 application_id INTEGER NOT NULL UNIQUE,
#                 job_id INTEGER NOT NULL,
#                 candidate_name VARCHAR(255),
#                 fit_score DECIMAL(5,2) CHECK (fit_score >= 0 AND fit_score <= 100),
#                 skill_score DECIMAL(5,2),
#                 experience_score DECIMAL(5,2),
#                 education_score DECIMAL(5,2),
#                 reasons JSONB,
#                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             );

#             CREATE INDEX IF NOT EXISTS idx_cs_application ON candidate_score(application_id);
#             CREATE INDEX IF NOT EXISTS idx_cs_job ON candidate_score(job_id);
#             CREATE INDEX IF NOT EXISTS idx_cs_score ON candidate_score(fit_score);
#             """

#             cursor.execute(create_table_query)
#             logger.info("Candidate score table created successfully")

#         except Exception as e:
#             logger.error(f"Error creating candidate score table: {e}")
#             raise

#     def save_candidate_score(self, score_data: CandidateScoreCreate, job_id: int, candidate_name: str = "Test Candidate") -> Optional[str]:
#         """Save candidate score menggunakan standalone database"""
#         try:
#             conn = get_db_connection()  # ← Use standalone connection
#             cursor = conn.cursor()

#             # Convert reasons to JSON string
#             import json
#             reasons_json = json.dumps(score_data.reasons) if score_data.reasons else None

#             insert_query = """
#             INSERT INTO candidate_score
#             (application_id, job_id, candidate_name, fit_score, skill_score, experience_score, education_score, reasons, updated_at)
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#             ON CONFLICT (application_id)
#             DO UPDATE SET
#                 fit_score = EXCLUDED.fit_score,
#                 skill_score = EXCLUDED.skill_score,
#                 experience_score = EXCLUDED.experience_score,
#                 education_score = EXCLUDED.education_score,
#                 reasons = EXCLUDED.reasons,
#                 updated_at = EXCLUDED.updated_at
#             RETURNING id
#             """

#             cursor.execute(insert_query, (
#                 score_data.application_id,
#                 job_id,
#                 candidate_name,
#                 float(score_data.fit_score),
#                 float(score_data.skill_score) if score_data.skill_score else None,
#                 float(score_data.experience_score) if score_data.experience_score else None,
#                 float(score_data.education_score) if score_data.education_score else None,
#                 reasons_json,
#                 datetime.utcnow()
#             ))

#             result = cursor.fetchone()
#             return result['id'] if result else None

#         except Exception as e:
#             logger.error(f"Error saving candidate score: {e}")
#             return None


#     def get_candidate_ranking(self, job_id: int, limit: int = 50, offset: int = 0,
#                         sort_order: str = "desc") -> List[Dict[str, Any]]:
#         """Get candidate ranking - STANDALONE tanpa join Odoo"""
#         try:
#             conn = self._get_connection()
#             cursor = conn.cursor()

#             # Validate sort order
#             sort_order = "DESC" if sort_order.lower() == "desc" else "ASC"

#             query = f"""
#             SELECT
#                 application_id,
#                 job_id,
#                 candidate_name,
#                 fit_score,
#                 skill_score,
#                 experience_score,
#                 education_score,
#                 reasons,
#                 updated_at
#             FROM candidate_score
#             WHERE job_id = %s
#             ORDER BY fit_score {sort_order}
#             LIMIT %s OFFSET %s
#             """

#             cursor.execute(query, (job_id, limit, offset))
#             results = cursor.fetchall()

#             return results

#         except Exception as e:
#             logger.error(f"Error getting candidate ranking: {e}")
#             return []

#     def get_candidate_score(self, application_id: int) -> Optional[Dict[str, Any]]:
#         """Get candidate score by application ID"""
#         try:
#             conn = self._get_connection()
#             cursor = conn.cursor()

#             query = """
#             SELECT * FROM candidate_score
#             WHERE application_id = %s
#             """

#             cursor.execute(query, (application_id,))
#             result = cursor.fetchone()

#             return result

#         except Exception as e:
#             logger.error(f"Error getting candidate score: {e}")
#             return None


#     def candidate_has_score(self, job_id: int) -> bool:
#         """Check if any candidate has score for a job - STANDALONE"""
#         try:
#             conn = self._get_connection()
#             cursor = conn.cursor()

#             query = """
#             SELECT COUNT(*) as count
#             FROM candidate_score
#             WHERE job_id = %s
#             """

#             cursor.execute(query, (job_id,))
#             result = cursor.fetchone()

#             return result['count'] > 0 if result else False

#         except Exception as e:
#             logger.error(f"Error checking candidate scores: {e}")
#             return False

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings
from app.schemas.candidate import CandidateScoreCreate
from app.services.database import get_db_connection  # Import yang benar

logger = logging.getLogger(__name__)


class CandidateService:
    def __init__(self):
        pass

    def create_candidate_score_table(self):
        """Create candidate_score table"""
        try:
            conn = get_db_connection()  # ← Gunakan fungsi yang ada
            cursor = conn.cursor()

            create_table_query = """
            CREATE TABLE IF NOT EXISTS candidate_score (
                id SERIAL PRIMARY KEY,
                application_id INTEGER NOT NULL UNIQUE,
                job_id INTEGER NOT NULL,
                candidate_name VARCHAR(255),
                fit_score DECIMAL(5,2) CHECK (fit_score >= 0 AND fit_score <= 100),
                skill_score DECIMAL(5,2),
                experience_score DECIMAL(5,2),
                education_score DECIMAL(5,2),
                reasons JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_cs_application ON candidate_score(application_id);
            CREATE INDEX IF NOT EXISTS idx_cs_job ON candidate_score(job_id);
            CREATE INDEX IF NOT EXISTS idx_cs_score ON candidate_score(fit_score);
            """

            cursor.execute(create_table_query)
            logger.info("Candidate score table created successfully")

        except Exception as e:
            logger.error(f"Error creating candidate score table: {e}")
            raise

    def save_candidate_score(
        self,
        score_data: CandidateScoreCreate,
        job_id: int,
        candidate_name: str = "Test Candidate",
    ) -> Optional[str]:
        """Save candidate score"""
        try:
            conn = get_db_connection()  # ← Gunakan fungsi yang ada
            cursor = conn.cursor()

            # Convert reasons to JSON string
            import json

            reasons_json = (
                json.dumps(score_data.reasons) if score_data.reasons else None
            )

            insert_query = """
            INSERT INTO candidate_score 
            (application_id, job_id, candidate_name, fit_score, skill_score, experience_score, education_score, reasons, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (application_id) 
            DO UPDATE SET 
                fit_score = EXCLUDED.fit_score,
                skill_score = EXCLUDED.skill_score,
                experience_score = EXCLUDED.experience_score,
                education_score = EXCLUDED.education_score,
                reasons = EXCLUDED.reasons,
                updated_at = EXCLUDED.updated_at
            RETURNING id
            """

            cursor.execute(
                insert_query,
                (
                    score_data.application_id,
                    job_id,
                    candidate_name,
                    float(score_data.fit_score),
                    float(score_data.skill_score) if score_data.skill_score else None,
                    float(score_data.experience_score)
                    if score_data.experience_score
                    else None,
                    float(score_data.education_score)
                    if score_data.education_score
                    else None,
                    reasons_json,
                    datetime.utcnow(),
                ),
            )

            result = cursor.fetchone()
            conn.commit()  # ← TAMBAH INI untuk commit changes
            return result["id"] if result else None

        except Exception as e:
            logger.error(f"Error saving candidate score: {e}")
            return None

    def get_candidate_ranking(
        self, job_id: int, limit: int = 50, offset: int = 0, sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get candidate ranking"""
        try:
            conn = get_db_connection()  # ← PERBAIKI: gunakan get_db_connection()
            cursor = conn.cursor()

            # Validate sort order
            sort_order = "DESC" if sort_order.lower() == "desc" else "ASC"

            query = f"""
            SELECT 
                application_id,
                job_id,
                candidate_name,
                fit_score,
                skill_score,
                experience_score,
                education_score,
                reasons,
                updated_at
            FROM candidate_score 
            WHERE job_id = %s
            ORDER BY fit_score {sort_order}
            LIMIT %s OFFSET %s
            """

            cursor.execute(query, (job_id, limit, offset))
            results = cursor.fetchall()

            return results

        except Exception as e:
            logger.error(f"Error getting candidate ranking: {e}")
            return []

    def get_candidate_score(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Get candidate score by application ID"""
        try:
            conn = get_db_connection()  # ← PERBAIKI
            cursor = conn.cursor()

            query = """
            SELECT * FROM candidate_score 
            WHERE application_id = %s
            """

            cursor.execute(query, (application_id,))
            result = cursor.fetchone()

            return result

        except Exception as e:
            logger.error(f"Error getting candidate score: {e}")
            return None

    def candidate_has_score(self, job_id: int) -> bool:
        """Check if any candidate has score for a job"""
        try:
            conn = get_db_connection()  # ← PERBAIKI
            cursor = conn.cursor()

            query = """
            SELECT COUNT(*) as count
            FROM candidate_score 
            WHERE job_id = %s
            """

            cursor.execute(query, (job_id,))
            result = cursor.fetchone()

            return result["count"] > 0 if result else False

        except Exception as e:
            logger.error(f"Error checking candidate scores: {e}")
            return False

    def create_candidate_for_job(
        self,
        job_id: int,
        name: str,
        email: str,
        phone: str = None,
        experience_years: int = None,
        skills: list = None,
        education: str = None,
    ) -> dict:
        """Create a new candidate application for a job"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert into application table
            cursor.execute(
                """
                    INSERT INTO applications (
                    job_id, candidate_name, email, phone, 
                    experience_years, skills, education, 
                    status, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'applied', CURRENT_TIMESTAMP)
                RETURNING id
                """,
                (
                    job_id,
                    name,
                    email,
                    phone,
                    experience_years,
                    skills if skills else None,
                    education,
                ),
            )
            result = cursor.fetchone()
            conn.commit()

            if result:
                return {"id": result["id"], "name": name, "email": email}
            return None

        except Exception as e:
            logger.error(f"Error creating candidate: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
