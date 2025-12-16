import logging
from typing import Optional
from datetime import datetime

from app.services.database import get_db_connection
from app.schemas.interview_feedback_schema import (
    InterviewFeedbackCreate,
    InterviewFeedbackUpdate,
    InterviewFeedbackResponse,
)

logger = logging.getLogger(__name__)


class InterviewFeedbackService:
    def __init__(self):
        pass

    def create_feedback(
        self, feedback_data: InterviewFeedbackCreate, created_by: int
    ) -> Optional[dict]:
        """
        Create new interview feedback for an application.
        Returns the created feedback or None if failed.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if feedback already exists for this application
            cursor.execute(
                "SELECT id FROM interview_feedbacks WHERE application_id = %s",
                (feedback_data.application_id,),
            )
            existing = cursor.fetchone()
            if existing:
                cursor.close()
                return {
                    "error": "Feedback sudah ada untuk application ini",
                    "code": 409,
                }

            # Check if application exists
            cursor.execute(
                "SELECT id FROM applications WHERE id = %s",
                (feedback_data.application_id,),
            )
            application = cursor.fetchone()
            if not application:
                cursor.close()
                return {"error": "Application tidak ditemukan", "code": 404}

            # Insert feedback
            cursor.execute(
                """
                INSERT INTO interview_feedbacks 
                (application_id, rating, feedback, created_by, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id, application_id, rating, feedback, created_by, created_at, updated_at
                """,
                (
                    feedback_data.application_id,
                    feedback_data.rating,
                    feedback_data.feedback,
                    created_by,
                ),
            )

            result = cursor.fetchone()
            cursor.close()

            logger.info(
                f"Created interview feedback for application {feedback_data.application_id}"
            )
            return dict(result)

        except Exception as e:
            logger.error(f"Error creating interview feedback: {e}")
            return {"error": str(e), "code": 500}

    def get_feedback_by_application(self, application_id: int) -> Optional[dict]:
        """Get feedback by application ID"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, application_id, rating, feedback, created_by, created_at, updated_at
                FROM interview_feedbacks
                WHERE application_id = %s
                """,
                (application_id,),
            )

            result = cursor.fetchone()
            cursor.close()

            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error getting interview feedback: {e}")
            return None

    def get_feedback_by_id(self, feedback_id: str) -> Optional[dict]:
        """Get feedback by feedback ID (UUID)"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, application_id, rating, feedback, created_by, created_at, updated_at
                FROM interview_feedbacks
                WHERE id = %s
                """,
                (feedback_id,),
            )

            result = cursor.fetchone()
            cursor.close()

            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error getting interview feedback by id: {e}")
            return None

    def update_feedback(
        self, feedback_id: str, update_data: InterviewFeedbackUpdate, updated_by: int
    ) -> Optional[dict]:
        """Update existing feedback"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if feedback exists
            cursor.execute(
                "SELECT id, created_by FROM interview_feedbacks WHERE id = %s",
                (feedback_id,),
            )
            existing = cursor.fetchone()
            if not existing:
                cursor.close()
                return {"error": "Feedback tidak ditemukan", "code": 404}

            # Build update query dynamically
            update_fields = []
            params = []

            if update_data.rating is not None:
                update_fields.append("rating = %s")
                params.append(update_data.rating)

            if update_data.feedback is not None:
                update_fields.append("feedback = %s")
                params.append(update_data.feedback)

            if not update_fields:
                cursor.close()
                return {"error": "Tidak ada data untuk diupdate", "code": 400}

            update_fields.append("updated_at = NOW()")
            params.append(feedback_id)

            query = f"""
                UPDATE interview_feedbacks
                SET {", ".join(update_fields)}
                WHERE id = %s
                RETURNING id, application_id, rating, feedback, created_by, created_at, updated_at
            """

            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()

            logger.info(f"Updated interview feedback {feedback_id}")
            return dict(result)

        except Exception as e:
            logger.error(f"Error updating interview feedback: {e}")
            return {"error": str(e), "code": 500}

    def update_feedback_by_application(
        self, application_id: int, update_data: InterviewFeedbackUpdate, updated_by: int
    ) -> Optional[dict]:
        """Update feedback by application ID (more-user-friendly)"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if feedback exists for this application
            cursor.execute(
                "SELECT id, created_by FROM interview_feedbacks WHERE application_id = %s",
                (application_id,),
            )
            existing = cursor.fetchone()
            if not existing:
                cursor.close()
                return {
                    "error": "Feedback tidak ditemukan untuk application ini",
                    "code": 404,
                }

            # Build update query dynamically
            update_fields = []
            params = []

            if update_data.rating is not None:
                update_fields.append("rating = %s")
                params.append(update_data.rating)

            if update_data.feedback is not None:
                update_fields.append("feedback = %s")
                params.append(update_data.feedback)

            if not update_fields:
                cursor.close()
                return {"error": "Tidak ada data untuk diupdate", "code": 400}

            # Always update timestamp for audit trail
            update_fields.append("updated_at = NOW()")
            params.append(application_id)

            query = f"""
                UPDATE interview_feedbacks
                SET {", ".join(update_fields)}
                WHERE application_id = %s
                RETURNING id, application_id, rating, feedback, created_by, created_at, updated_at
            """

            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()

            logger.info(
                f"Update interview feedback for application {application_id} by user {updated_by}"
            )
            return dict(result)

        except Exception as e:
            logger.error(f"Error updating interview feedback by application: {e}")
            return {"error": str(e), "code": 500}


# Singleton instance
interview_feedback_service = InterviewFeedbackService()
