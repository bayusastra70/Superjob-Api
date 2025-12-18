import logging
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.database import get_db_connection
from app.schemas.chat import MessageCreate, MessageStatus
from app.services.websocket_manager import websocket_manager
from app.services.activity_log_service import activity_log_service

# Import notification service jika ada
try:
    from app.services.notification_service import notification_service
except ImportError:
    notification_service = None

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        pass

    def get_chat_threads(
        self, user_id: int, user_type: str = "employer"
    ) -> List[Dict[str, Any]]:
        """Get chat threads for a user"""
        try:
            logger.info(f"USER ID => {user_id}")
            conn = get_db_connection()
            cursor = conn.cursor()

            if user_type == "employer":
                query = """
                SELECT  
                    ct.id as id,
                    ct.application_id as application_id,
                    ct.job_id as job_id,
                    ct.employer_id as employer_id,
                    ct.candidate_id as candidate_id,
                    em.full_name as employer_name,
                    can.full_name as candidate_name,
                    j.title as job_title,
                    ct.last_message as last_message,
                    ct.last_message_at as last_message_at,
                    ct.unread_count_employer as unread_count_employer,
                    ct.unread_count_candidate as unread_count_candidate,
                    ct.created_at as created_at,
                    ct.updated_at as updated_at
                FROM chat_threads ct
                JOIN users em ON ct.employer_id = em.id
                JOIN users can ON ct.candidate_id = can.id
                JOIN jobs j ON ct.job_id = j.id
                WHERE employer_id = %s
                ORDER BY ct.updated_at DESC
                """
            else:  # candidate
                query = """
                SELECT  
                    ct.id as id,
                    ct.application_id as application_id,
                    ct.job_id as job_id,
                    ct.employer_id as employer_id,
                    ct.candidate_id as candidate_id,
                    em.full_name as employer_name,
                    can.full_name as candidate_name,
                    j.title as job_title,
                    ct.last_message as last_message,
                    ct.last_message_at as last_message_at,
                    ct.unread_count_employer as unread_count_employer,
                    ct.unread_count_candidate as unread_count_candidate,
                    ct.created_at as created_at,
                    ct.updated_at as updated_at
                FROM chat_threads ct
                JOIN users em ON ct.employer_id = em.id
                JOIN users can ON ct.candidate_id = can.id
                JOIN jobs j ON ct.job_id = j.id
                WHERE candidate_id = %s
                ORDER BY ct.updated_at DESC
                """

            cursor.execute(query, (user_id,))
            threads = cursor.fetchall()
            logger.info(f"THREADS {threads}")
            return threads

        except Exception as e:
            logger.error(f"Error getting chat threads: {e}")
            return []

    def get_thread_messages(
        self, thread_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get messages in a thread"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT * FROM messages 
            WHERE thread_id = %s 
            ORDER BY created_at ASC
            LIMIT %s
            """

            cursor.execute(query, (thread_id, limit))
            messages = cursor.fetchall()

            return messages

        except Exception as e:
            logger.error(f"Error getting thread messages: {e}")
            return []

    # async def send_message(self, sender_id: int, sender_name: str, message_data: MessageCreate) -> Optional[Dict[str, Any]]:
    #     """Send a new message with WebSocket broadcast"""
    #     try:
    #         conn = get_db_connection()
    #         cursor = conn.cursor()

    #         # Get receiver info
    #         cursor.execute("""
    #         SELECT
    #             CASE WHEN %s = employer_id THEN candidate_id ELSE employer_id END as receiver_id,
    #             CASE WHEN %s = employer_id THEN candidate_name ELSE 'Employer' END as receiver_name,
    #             employer_id,
    #             candidate_id,
    #             job_id
    #         FROM chat_threads WHERE id = %s
    #         """, (sender_id, sender_id, message_data.thread_id))

    #         thread_info = cursor.fetchone()
    #         if not thread_info:
    #             logger.error(f"Thread not found: {message_data.thread_id}")
    #             return None

    #         receiver_id = thread_info['receiver_id']
    #         receiver_name = thread_info['receiver_name']

    #         # Insert message
    #         message_id = str(uuid.uuid4())
    #         insert_query = """
    #         INSERT INTO messages
    #         (id, thread_id, sender_id, receiver_id, sender_name, receiver_name,
    #          message_text, status, is_ai_suggestion)
    #         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    #         RETURNING id, created_at
    #         """

    #         cursor.execute(insert_query, (
    #             message_id,
    #             message_data.thread_id,
    #             sender_id,
    #             receiver_id,
    #             sender_name,
    #             receiver_name,
    #             message_data.message_text,
    #             MessageStatus.SENT.value,
    #             message_data.is_ai_suggestion
    #         ))

    #         message_result = cursor.fetchone()

    #         # Update thread last message and unread count
    #         if sender_id == thread_info.get('employer_id'):
    #             # Employer sent, increment candidate unread
    #             update_query = """
    #             UPDATE chat_threads
    #             SET last_message = %s,
    #                 last_message_at = %s,
    #                 unread_count_candidate = unread_count_candidate + 1,
    #                 updated_at = CURRENT_TIMESTAMP
    #             WHERE id = %s
    #             RETURNING unread_count_candidate
    #             """
    #         else:
    #             # Candidate sent, increment employer unread
    #             update_query = """
    #             UPDATE chat_threads
    #             SET last_message = %s,
    #                 last_message_at = %s,
    #                 unread_count_employer = unread_count_employer + 1,
    #                 updated_at = CURRENT_TIMESTAMP
    #             WHERE id = %s
    #             RETURNING unread_count_employer
    #             """

    #         cursor.execute(update_query, (message_data.message_text[:100],
    #                                     message_result['created_at'],
    #                                     message_data.thread_id))

    #         thread_update = cursor.fetchone()

    #         conn.commit()

    #         # Prepare message data for WebSocket
    #         message_data_response = {
    #             "id": message_id,
    #             "thread_id": message_data.thread_id,
    #             "sender_id": sender_id,
    #             "sender_name": sender_name,
    #             "receiver_id": receiver_id,
    #             "receiver_name": receiver_name,
    #             "message_text": message_data.message_text,
    #             "status": MessageStatus.SENT.value,
    #             "is_ai_suggestion": message_data.is_ai_suggestion,
    #             "created_at": message_result['created_at'].isoformat(),
    #             "unread_count": thread_update['unread_count_employer'] if sender_id != thread_info['employer_id'] else thread_update['unread_count_candidate']
    #         }

    #         # Broadcast via WebSocket
    #         await websocket_manager.broadcast_new_message(
    #             message_data.thread_id,
    #             message_data_response,
    #             sender_id
    #         )

    #         logger.info(f"Message sent and broadcasted: {message_id}")

    #         activity_log_service.log_new_message(
    #             employer_id=thread_info.get("employer_id"),
    #             job_id=thread_info.get("job_id"),
    #             applicant_id=thread_info.get("candidate_id"),
    #             message_id=message_id,
    #             sender_name=sender_name,
    #             receiver_name=receiver_name,
    #             message_preview=message_data.message_text,
    #             thread_id=message_data.thread_id,
    #         )

    #         return message_data_response

    #     except Exception as e:
    #         logger.error(f"Error sending message: {e}")
    #         return None

    # async def send_message(self, sender_id: str, sender_name: str, message_data: MessageCreate):
    #     """Send a new message with notification"""
    #     try:
    #         conn = get_db_connection()
    #         cursor = conn.cursor()

    #         # Get thread info with more details
    #         cursor.execute("""
    #             SELECT ct.candidate_id, ct.employer_id, ct.candidate_name,
    #                 ct.unread_count_employer, ct.unread_count_candidate
    #             FROM chat_threads ct
    #             WHERE ct.id = %s
    #         """, (message_data.thread_id,))

    #         thread = cursor.fetchone()

    #         if not thread:
    #             conn.close()
    #             return None

    #         # Determine receiver
    #         receiver_id = None
    #         receiver_name = None
    #         receiver_role = None

    #         if str(sender_id) == str(thread['candidate_id']):
    #             # Pengirim adalah candidate, penerima employer
    #             receiver_id = thread['employer_id']
    #             receiver_name = "Employer"  # Default name
    #             receiver_role = "employer"
    #         else:
    #             # Pengirim adalah employer, penerima candidate
    #             receiver_id = thread['candidate_id']
    #             receiver_name = thread.get('candidate_name', 'Candidate')
    #             receiver_role = "candidate"

    #         # Save message
    #         message_id = str(uuid.uuid4())
    #         created_at = datetime.utcnow()

    #         cursor.execute("""
    #             INSERT INTO messages
    #             (id, thread_id, sender_id, sender_name, receiver_id, receiver_name,
    #             message_text, is_ai_suggestion, status, created_at)
    #             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    #         """, (
    #             message_id,
    #             message_data.thread_id,
    #             sender_id,
    #             sender_name,
    #             receiver_id,
    #             receiver_name,
    #             message_data.message_text,
    #             message_data.is_ai_suggestion,
    #             MessageStatus.SENT.value,
    #             created_at
    #         ))

    #         # Update thread last_message and unread count
    #         if receiver_role == "employer":
    #             cursor.execute("""
    #                 UPDATE chat_threads
    #                 SET last_message = %s,
    #                     last_message_at = %s,
    #                     unread_count_employer = unread_count_employer + 1,
    #                     updated_at = CURRENT_TIMESTAMP
    #                 WHERE id = %s
    #             """, (message_data.message_text[:100], created_at, message_data.thread_id))
    #         else:
    #             cursor.execute("""
    #                 UPDATE chat_threads
    #                 SET last_message = %s,
    #                     last_message_at = %s,
    #                     unread_count_candidate = unread_count_candidate + 1,
    #                     updated_at = CURRENT_TIMESTAMP
    #                 WHERE id = %s
    #             """, (message_data.message_text[:100], created_at, message_data.thread_id))

    #         conn.commit()

    #         # **TRIGGER NOTIFICATION** - Only if user is receiver
    #         await self._trigger_notification(
    #             thread_id=message_data.thread_id,
    #             sender_id=str(sender_id),
    #             sender_name=sender_name,
    #             receiver_id=str(receiver_id),
    #             receiver_name=receiver_name,
    #             message_text=message_data.message_text,
    #             receiver_role=receiver_role
    #         )

    #         # Prepare WebSocket data
    #         websocket_data = {
    #             "type": "message:new",
    #             "message_id": message_id,
    #             "thread_id": message_data.thread_id,
    #             "sender_id": str(sender_id),
    #             "sender_name": sender_name,
    #             "receiver_id": str(receiver_id),
    #             "receiver_name": receiver_name,
    #             "message_text": message_data.message_text,
    #             "is_ai_suggestion": message_data.is_ai_suggestion,
    #             "status": MessageStatus.SENT.value,
    #             "created_at": created_at.isoformat(),
    #             "receiver_role": receiver_role
    #         }

    #         # Broadcast via WebSocket
    #         await websocket_manager.broadcast_to_thread(
    #             message_data.thread_id,
    #             websocket_data
    #         )

    #         # Juga broadcast menggunakan fungsi yang sudah ada (jika ada)
    #         try:
    #             await websocket_manager.broadcast_new_message(
    #                 message_data.thread_id,
    #                 websocket_data,
    #                 sender_id
    #             )
    #         except AttributeError:
    #             # Jika method tidak ada, skip saja
    #             pass

    #         # Log activity
    #         try:
    #             activity_log_service.log_new_message(
    #                 employer_id=thread['employer_id'],
    #                 job_id=None,  # Tambahkan jika ada di data
    #                 applicant_id=thread['candidate_id'],
    #                 message_id=message_id,
    #                 sender_name=sender_name,
    #                 receiver_name=receiver_name,
    #                 message_preview=message_data.message_text[:100],
    #                 thread_id=message_data.thread_id,
    #             )
    #         except Exception as e:
    #             logger.error(f"Error logging activity: {e}")

    #         conn.close()

    #         return {
    #             "message_id": message_id,
    #             "thread_id": message_data.thread_id,
    #             "sender_id": sender_id,
    #             "receiver_id": receiver_id,
    #             "receiver_role": receiver_role
    #         }

    #     except Exception as e:
    #         logger.error(f"Error sending message: {e}")
    #         if 'conn' in locals():
    #             conn.close()
    #         return None

    async def send_message(
        self, sender_id: str, sender_name: str, message_data: MessageCreate
    ):
        """Send a new message with notification"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Convert sender_id ke integer untuk query database
            sender_id_int = int(sender_id) if sender_id else None

            # Get thread info with more details
            cursor.execute(
                """
                SELECT ct.candidate_id, ct.employer_id, ct.candidate_name,
                    ct.unread_count_employer, ct.unread_count_candidate
                FROM chat_threads ct 
                WHERE ct.id = %s
            """,
                (message_data.thread_id,),
            )

            thread = cursor.fetchone()

            if not thread:
                conn.close()
                return None

            # Determine receiver - PERBAIKAN: bandingkan sebagai string
            receiver_id = None
            receiver_name = None
            receiver_role = None

            # Convert database IDs to string for comparison
            candidate_id_str = str(thread["candidate_id"])
            employer_id_str = str(thread["employer_id"])

            if sender_id == candidate_id_str:
                # Pengirim adalah candidate, penerima employer
                receiver_id = str(thread["employer_id"])  # Simpan sebagai string
                receiver_name = "Employer"
                receiver_role = "employer"
                sender_is_candidate = True
            elif sender_id == employer_id_str:
                # Pengirim adalah employer, penerima candidate
                receiver_id = str(thread["candidate_id"])  # Simpan sebagai string
                receiver_name = thread.get("candidate_name", "Candidate")
                receiver_role = "candidate"
                sender_is_candidate = False
            else:
                logger.error(
                    f"Sender {sender_id} not part of thread {message_data.thread_id}"
                )
                conn.close()
                return None

            # Save message - GUNAKAN sender_id_int untuk database
            message_id = str(uuid.uuid4())
            created_at = datetime.utcnow()

            cursor.execute(
                """
                INSERT INTO messages 
                (id, thread_id, sender_id, sender_name, receiver_id, receiver_name, 
                message_text, is_ai_suggestion, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    message_id,
                    message_data.thread_id,
                    sender_id_int,  # Integer untuk database
                    sender_name,
                    int(receiver_id),  # Integer untuk database
                    receiver_name,
                    message_data.message_text,
                    message_data.is_ai_suggestion,
                    MessageStatus.SENT.value,
                    created_at,
                ),
            )

            # Update thread last_message and unread count
            if receiver_role == "employer":
                cursor.execute(
                    """
                    UPDATE chat_threads 
                    SET last_message = %s, 
                        last_message_at = %s, 
                        unread_count_employer = unread_count_employer + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """,
                    (
                        message_data.message_text[:100],
                        created_at,
                        message_data.thread_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    UPDATE chat_threads 
                    SET last_message = %s, 
                        last_message_at = %s, 
                        unread_count_candidate = unread_count_candidate + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """,
                    (
                        message_data.message_text[:100],
                        created_at,
                        message_data.thread_id,
                    ),
                )

            conn.commit()

            # **TRIGGER NOTIFICATION** - Only if user is receiver
            await self._trigger_notification(
                thread_id=message_data.thread_id,
                sender_id=str(sender_id),  # Pastikan string
                sender_name=sender_name,
                receiver_id=receiver_id,  # Sudah string
                receiver_name=receiver_name,
                message_text=message_data.message_text,
                receiver_role=receiver_role,
            )

            # Prepare WebSocket data
            websocket_data = {
                "type": "message:new",
                "message_id": message_id,
                "thread_id": message_data.thread_id,
                "sender_id": sender_id,  # String
                "sender_name": sender_name,
                "receiver_id": receiver_id,  # String
                "receiver_name": receiver_name,
                "message_text": message_data.message_text,
                "is_ai_suggestion": message_data.is_ai_suggestion,
                "status": MessageStatus.SENT.value,
                "created_at": created_at.isoformat(),
                "receiver_role": receiver_role,
            }

            # Broadcast via WebSocket
            await websocket_manager.broadcast_to_thread(
                message_data.thread_id, websocket_data
            )

            # Log activity
            try:
                activity_log_service.log_new_message(
                    employer_id=thread["employer_id"],
                    job_id=None,
                    applicant_id=thread["candidate_id"],
                    message_id=message_id,
                    sender_name=sender_name,
                    receiver_name=receiver_name,
                    message_preview=message_data.message_text[:100],
                    thread_id=message_data.thread_id,
                )
            except Exception as e:
                logger.error(f"Error logging activity: {e}")

            conn.close()

            return {
                "message_id": message_id,
                "thread_id": message_data.thread_id,
                "sender_id": sender_id,  # String
                "receiver_id": receiver_id,  # String
                "receiver_role": receiver_role,
            }

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            if "conn" in locals():
                conn.close()
            return None

    async def _trigger_notification(
        self,
        thread_id: str,
        sender_id: str,
        sender_name: str,
        receiver_id: str,
        receiver_name: str,
        message_text: str,
        receiver_role: str,
    ):
        """Trigger notification for new message"""
        try:
            from app.services.notification_service import notification_service

            # Prepare notification data
            notification_data = {
                "user_id": receiver_id,
                "title": f"Pesan baru dari {sender_name}",
                "message": message_text[:100]
                + ("..." if len(message_text) > 100 else ""),
                "notification_type": "message",
                "data": {
                    "thread_id": thread_id,
                    "sender_id": sender_id,
                    "sender_name": sender_name,
                    "receiver_id": receiver_id,
                    "receiver_name": receiver_name,
                    "receiver_role": receiver_role,
                    "message_preview": message_text[:100],
                },
                "thread_id": thread_id,
            }

            # Add to notification queue
            await notification_service.add_to_queue(notification_data)

            # Also send in-app toast via WebSocket
            await websocket_manager.send_personal_message(
                {
                    "type": "notification:new",
                    "notification": {
                        "id": str(uuid.uuid4()),  # Generate ID untuk FE
                        "title": notification_data["title"],
                        "message": notification_data["message"],
                        "thread_id": thread_id,
                        "sender_id": sender_id,
                        "sender_name": sender_name,
                        "receiver_id": receiver_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "receiver_role": receiver_role,
                    },
                },
                receiver_id,
            )

            logger.info(
                f"Notification triggered for user {receiver_id} (role: {receiver_role})"
            )

        except ImportError:
            logger.warning("Notification service not available, skipping notification")
        except Exception as e:
            logger.error(f"Error triggering notification: {e}")

    # async def mark_messages_as_seen(self, thread_id: str, user_id: int) -> bool:
    #     """Mark messages as seen and reset unread count with WebSocket broadcast"""
    #     try:
    #         conn = get_db_connection()
    #         cursor = conn.cursor()

    #         # Get thread info first
    #         cursor.execute("""
    #         SELECT employer_id, candidate_id FROM chat_threads WHERE id = %s
    #         """, (thread_id,))
    #         thread_info = cursor.fetchone()

    #         if not thread_info:
    #             return False

    #         # Update messages status
    #         update_messages = """
    #         UPDATE messages
    #         SET status = 'seen'
    #         WHERE thread_id = %s
    #           AND receiver_id = %s
    #           AND status IN ('sent', 'delivered')
    #         RETURNING COUNT(*) as updated_count
    #         """
    #         cursor.execute(update_messages, (thread_id, user_id))
    #         updated_count = cursor.fetchone()['updated_count']

    #         # Update unread count in thread
    #         update_thread = """
    #         UPDATE chat_threads
    #         SET
    #             unread_count_employer = CASE WHEN %s = employer_id THEN 0 ELSE unread_count_employer END,
    #             unread_count_candidate = CASE WHEN %s = candidate_id THEN 0 ELSE unread_count_candidate END,
    #             updated_at = CURRENT_TIMESTAMP
    #         WHERE id = %s
    #         RETURNING unread_count_employer, unread_count_candidate
    #         """
    #         cursor.execute(update_thread, (user_id, user_id, thread_id))
    #         unread_counts = cursor.fetchone()

    #         conn.commit()

    #         # Broadcast status update via WebSocket
    #         status_data = {
    #             "thread_id": thread_id,
    #             "user_id": user_id,
    #             "updated_count": updated_count,
    #             "unread_counts": unread_counts
    #         }
    #         await websocket_manager.broadcast_status_update(
    #             thread_id, user_id, "seen", status_data
    #         )

    #         logger.info(f"Messages marked as seen for user {user_id} in thread {thread_id}")

    #         return True

    #     except Exception as e:
    #         logger.error(f"Error marking messages as seen: {e}")
    #         return False

    async def mark_messages_as_seen(self, thread_id: str, user_id: int) -> bool:
        """Mark messages as seen and reset unread count with WebSocket broadcast"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get thread info first
            cursor.execute(
                """
            SELECT employer_id, candidate_id FROM chat_threads WHERE id = %s
            """,
                (thread_id,),
            )
            thread_info = cursor.fetchone()

            if not thread_info:
                conn.close()
                return False

            # Update messages status
            # Tidak bisa pakai RETURNING COUNT(*), pakai cursor.rowcount
            update_messages = """
            UPDATE messages 
            SET status = 'seen' 
            WHERE thread_id = %s 
            AND receiver_id = %s 
            AND status IN ('sent', 'delivered')
            """
            cursor.execute(update_messages, (thread_id, user_id))
            updated_count = cursor.rowcount  # Jumlah baris yang diupdate

            # Update unread count in thread
            update_thread = """
            UPDATE chat_threads 
            SET 
                unread_count_employer = CASE WHEN %s = employer_id THEN 0 ELSE unread_count_employer END,
                unread_count_candidate = CASE WHEN %s = candidate_id THEN 0 ELSE unread_count_candidate END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING unread_count_employer, unread_count_candidate
            """
            cursor.execute(update_thread, (user_id, user_id, thread_id))
            unread_counts = cursor.fetchone()

            conn.commit()

            # Broadcast status update via WebSocket
            status_data = {
                "thread_id": thread_id,
                "user_id": user_id,
                "updated_count": updated_count,
                "unread_counts": dict(unread_counts) if unread_counts else {},
            }

            try:
                await websocket_manager.broadcast_status_update(
                    thread_id, user_id, "seen", status_data
                )
            except AttributeError:
                # Jika method tidak ada, gunakan broadcast_to_thread
                await websocket_manager.broadcast_to_thread(
                    thread_id,
                    {
                        "type": "message:status:update",
                        "thread_id": thread_id,
                        "user_id": user_id,
                        "status": "seen",
                        "updated_count": updated_count,
                    },
                )

            logger.info(
                f"Messages marked as seen for user {user_id} in thread {thread_id}"
            )

            return True

        except Exception as e:
            logger.error(f"Error marking messages as seen: {e}")
            return False
        finally:
            if "conn" in locals():
                conn.close()

    def create_thread(self, thread_data: Dict[str, Any]) -> Optional[str]:
        """Create a new chat thread"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            thread_id = str(uuid.uuid4())
            insert_query = """
            INSERT INTO chat_threads 
            (id, application_id, job_id, employer_id, candidate_id, candidate_name, job_title)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """

            cursor.execute(
                insert_query,
                (
                    thread_id,
                    thread_data["application_id"],
                    thread_data["job_id"],
                    thread_data["employer_id"],
                    thread_data["candidate_id"],
                    thread_data.get("candidate_name"),
                    thread_data.get("job_title"),
                ),
            )

            conn.commit()
            logger.info(f"Chat thread created: {thread_id}")

            return thread_id

        except Exception as e:
            logger.error(f"Error creating chat thread: {e}")
            return None

    def get_ai_suggestions(self, thread_id: str, limit: int = 10) -> List[str]:
        """Generate AI suggestions based on chat context"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get recent messages for context
            query = """
            SELECT message_text, sender_id 
            FROM messages 
            WHERE thread_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """

            cursor.execute(query, (thread_id, limit))
            messages = cursor.fetchall()

            if not messages:
                return ["Tidak ada saran balasan"]

            # Simple AI logic (dummy implementation)
            # In real app, integrate with LLM API
            last_message = messages[0]["message_text"].lower()

            # Basic keyword matching for demo
            suggestions = []

            if any(word in last_message for word in ["halo", "hello", "hi", "hey"]):
                suggestions = [
                    "Halo! Ada yang bisa saya bantu?",
                    "Selamat pagi/siang/sore!",
                    "Halo, terima kasih telah menghubungi",
                ]
            elif any(word in last_message for word in ["interview", "wawancara"]):
                suggestions = [
                    "Kapan Anda available untuk interview?",
                    "Lokasi interview di kantor kami",
                    "Interview akan dilakukan via Zoom",
                ]
            elif any(word in last_message for word in ["terima kasih", "thanks"]):
                suggestions = [
                    "Sama-sama!",
                    "Terima kasih kembali",
                    "Dengan senang hati",
                ]
            elif any(word in last_message for word in ["gaji", "salary", "uang"]):
                suggestions = [
                    "Range gaji untuk posisi ini adalah...",
                    "Bisa kita diskusikan lebih lanjut",
                    "Package termasuk benefits dan bonus",
                ]
            else:
                suggestions = [
                    "Bisa Anda jelaskan lebih detail?",
                    "Saya akan cek terlebih dahulu",
                    "Apakah ada pertanyaan lain?",
                ]

            return suggestions[:3]  # Return max 3 suggestions

        except Exception as e:
            logger.error(f"Error generating AI suggestions: {e}")
            return []
