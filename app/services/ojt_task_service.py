from loguru import logger
from typing import List, Dict, Any, Optional

from app.services.database import get_db_connection, release_connection
from datetime import datetime

class OjtTaskService:
    def __init__(self):
        pass

    def get_tasks_by_program(self, program_id: int, user_id: int = None) -> List[Dict[str, Any]]:
        """
        Get all tasks for a program. 
        If user_id is provided, includes their submission status and score.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    t.*,
                    sub.status as submission_status,
                    sub.score as my_score
                FROM ojt_tasks t
                LEFT JOIN ojt_task_submissions sub ON t.id = sub.task_id AND sub.talent_id = %s
                WHERE t.program_id = %s
                ORDER BY t.created_at DESC, t.order_number ASC
            """
            cursor.execute(query, (user_id, program_id))
            tasks = cursor.fetchall()
            return [dict(row) for row in tasks]

        except Exception as e:
            logger.error(f"Error getting OJT tasks for program {program_id}: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def submit_task(self, task_id: int, talent_id: int, content: str = None, file_url: str = None) -> Dict[str, Any]:
        """Submit a task answer."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Upsert logic: if exists update, else insert
            # Check existing first
            check_query = """
                SELECT id FROM ojt_task_submissions 
                WHERE task_id = %s AND talent_id = %s
            """
            cursor.execute(check_query, (task_id, talent_id))
            existing = cursor.fetchone()

            if existing:
                update_query = """
                    UPDATE ojt_task_submissions 
                    SET content = %s, file_url = %s, status = 'submitted', submitted_at = NOW()
                    WHERE id = %s
                    RETURNING id, submitted_at, status
                """
                cursor.execute(update_query, (content, file_url, existing['id']))
            else:
                insert_query = """
                    INSERT INTO ojt_task_submissions (task_id, talent_id, content, file_url, status)
                    VALUES (%s, %s, %s, %s, 'submitted')
                    RETURNING id, submitted_at, status
                """
                cursor.execute(insert_query, (task_id, talent_id, content, file_url))
            
            conn.commit()
            result = cursor.fetchone()
            return dict(result)

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error submitting task {task_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def get_my_submission(self, task_id: int, talent_id: int) -> Optional[Dict[str, Any]]:
        """Get user submission for a specific task."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    s.*,
                    u.full_name as talent_name
                FROM ojt_task_submissions s
                JOIN users u ON s.talent_id = u.id
                WHERE s.task_id = %s AND s.talent_id = %s
            """
            cursor.execute(query, (task_id, talent_id))
            submission = cursor.fetchone()
            
            return dict(submission) if submission else None

        except Exception as e:
            logger.error(f"Error getting submission for task {task_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

    def get_my_scores(self, program_id: int, talent_id: int) -> List[Dict[str, Any]]:
        """Get all scores and feedback for a user in a program."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    t.id as task_id,
                    t.title as task_title,
                    t.max_score,
                    s.score as my_score,
                    s.feedback,
                    s.status,
                    s.submitted_at
                FROM ojt_tasks t
                LEFT JOIN ojt_task_submissions s ON t.id = s.task_id AND s.talent_id = %s
                WHERE t.program_id = %s
                ORDER BY t.created_at DESC
            """
            cursor.execute(query, (talent_id, program_id))
            scores = cursor.fetchall()
            
            return [dict(row) for row in scores]

        except Exception as e:
            logger.error(f"Error getting scores: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                release_connection(conn)

ojt_task_service = OjtTaskService()
