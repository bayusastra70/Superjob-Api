import logging
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.database import get_db_connection
from app.schemas.chat import MessageCreate, MessageStatus
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        pass
    
    def get_chat_threads(self, user_id: int, user_type: str = "employer") -> List[Dict[str, Any]]:
        """Get chat threads for a user"""
        try:
            logger.info(f"USER ID => {user_id}");
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if user_type == "employer":
                query = """
                SELECT * FROM chat_threads 
                WHERE employer_id = %s 
                ORDER BY updated_at DESC
                """
            else:  # candidate
                query = """
                SELECT * FROM chat_threads 
                WHERE candidate_id = %s 
                ORDER BY updated_at DESC
                """
            
            cursor.execute(query, (user_id,))
            threads = cursor.fetchall()
            
            return threads
            
        except Exception as e:
            logger.error(f"Error getting chat threads: {e}")
            return []
    
    def get_thread_messages(self, thread_id: str, limit: int = 100) -> List[Dict[str, Any]]:
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
    
    # def send_message(self, sender_id: int, sender_name: str, message_data: MessageCreate) -> Optional[str]:
    #     """Send a new message"""
    #     try:
    #         conn = get_db_connection()
    #         cursor = conn.cursor()
            
    #         # Get receiver info (simplified - in real app, get from users table)
    #         cursor.execute("""
    #         SELECT 
    #             CASE WHEN %s = employer_id THEN candidate_id ELSE employer_id END as receiver_id,
    #             CASE WHEN %s = employer_id THEN candidate_name ELSE 'Employer' END as receiver_name
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
    #         (id, thread_id, sender_id, receiver_id, sender_name, receiver_name, message_text, status, is_ai_suggestion)
    #         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    #         RETURNING id
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
            
    #         # Update thread last message and unread count
    #         if sender_id == thread_info.get('employer_id'):
    #             # Employer sent, increment candidate unread
    #             update_query = """
    #             UPDATE chat_threads 
    #             SET last_message = %s, 
    #                 last_message_at = CURRENT_TIMESTAMP,
    #                 unread_count_candidate = unread_count_candidate + 1,
    #                 updated_at = CURRENT_TIMESTAMP
    #             WHERE id = %s
    #             """
    #         else:
    #             # Candidate sent, increment employer unread
    #             update_query = """
    #             UPDATE chat_threads 
    #             SET last_message = %s, 
    #                 last_message_at = CURRENT_TIMESTAMP,
    #                 unread_count_employer = unread_count_employer + 1,
    #                 updated_at = CURRENT_TIMESTAMP
    #             WHERE id = %s
    #             """
            
    #         cursor.execute(update_query, (message_data.message_text[:100], message_data.thread_id))
            
    #         conn.commit()
    #         logger.info(f"Message sent: {message_id} in thread {message_data.thread_id}")
            
    #         return message_id
            
    #     except Exception as e:
    #         logger.error(f"Error sending message: {e}")
    #         return None
    
    # def mark_messages_as_seen(self, thread_id: str, user_id: int) -> bool:
    #     """Mark messages as seen and reset unread count"""
    #     try:
    #         conn = get_db_connection()
    #         cursor = conn.cursor()
            
    #         # Update messages status
    #         update_messages = """
    #         UPDATE messages 
    #         SET status = 'seen' 
    #         WHERE thread_id = %s 
    #           AND receiver_id = %s 
    #           AND status IN ('sent', 'delivered')
    #         """
    #         cursor.execute(update_messages, (thread_id, user_id))
            
    #         # Update unread count in thread
    #         update_thread = """
    #         UPDATE chat_threads 
    #         SET 
    #             unread_count_employer = CASE WHEN %s = employer_id THEN 0 ELSE unread_count_employer END,
    #             unread_count_candidate = CASE WHEN %s = candidate_id THEN 0 ELSE unread_count_candidate END
    #         WHERE id = %s
    #         """
    #         cursor.execute(update_thread, (user_id, user_id, thread_id))
            
    #         conn.commit()
    #         logger.info(f"Messages marked as seen for user {user_id} in thread {thread_id}")
            
    #         return True
            
    #     except Exception as e:
    #         logger.error(f"Error marking messages as seen: {e}")
    #         return False

    async def send_message(self, sender_id: int, sender_name: str, message_data: MessageCreate) -> Optional[Dict[str, Any]]:
        """Send a new message with WebSocket broadcast"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get receiver info
            cursor.execute("""
            SELECT 
                CASE WHEN %s = employer_id THEN candidate_id ELSE employer_id END as receiver_id,
                CASE WHEN %s = employer_id THEN candidate_name ELSE 'Employer' END as receiver_name,
                employer_id,
                candidate_id
            FROM chat_threads WHERE id = %s
            """, (sender_id, sender_id, message_data.thread_id))
            
            thread_info = cursor.fetchone()
            if not thread_info:
                logger.error(f"Thread not found: {message_data.thread_id}")
                return None
            
            receiver_id = thread_info['receiver_id']
            receiver_name = thread_info['receiver_name']
            
            # Insert message
            message_id = str(uuid.uuid4())
            insert_query = """
            INSERT INTO messages 
            (id, thread_id, sender_id, receiver_id, sender_name, receiver_name, 
             message_text, status, is_ai_suggestion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            """
            
            cursor.execute(insert_query, (
                message_id,
                message_data.thread_id,
                sender_id,
                receiver_id,
                sender_name,
                receiver_name,
                message_data.message_text,
                MessageStatus.SENT.value,
                message_data.is_ai_suggestion
            ))
            
            message_result = cursor.fetchone()
            
            # Update thread last message and unread count
            if sender_id == thread_info.get('employer_id'):
                # Employer sent, increment candidate unread
                update_query = """
                UPDATE chat_threads 
                SET last_message = %s, 
                    last_message_at = %s,
                    unread_count_candidate = unread_count_candidate + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING unread_count_candidate
                """
            else:
                # Candidate sent, increment employer unread
                update_query = """
                UPDATE chat_threads 
                SET last_message = %s, 
                    last_message_at = %s,
                    unread_count_employer = unread_count_employer + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING unread_count_employer
                """
            
            cursor.execute(update_query, (message_data.message_text[:100], 
                                        message_result['created_at'], 
                                        message_data.thread_id))
            
            thread_update = cursor.fetchone()
            
            conn.commit()
            
            # Prepare message data for WebSocket
            message_data_response = {
                "id": message_id,
                "thread_id": message_data.thread_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "receiver_id": receiver_id,
                "receiver_name": receiver_name,
                "message_text": message_data.message_text,
                "status": MessageStatus.SENT.value,
                "is_ai_suggestion": message_data.is_ai_suggestion,
                "created_at": message_result['created_at'].isoformat(),
                "unread_count": thread_update['unread_count_employer'] if sender_id != thread_info['employer_id'] else thread_update['unread_count_candidate']
            }
            
            # Broadcast via WebSocket
            await websocket_manager.broadcast_new_message(
                message_data.thread_id,
                message_data_response,
                sender_id
            )
            
            logger.info(f"Message sent and broadcasted: {message_id}")
            
            return message_data_response
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
    
    async def mark_messages_as_seen(self, thread_id: str, user_id: int) -> bool:
        """Mark messages as seen and reset unread count with WebSocket broadcast"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get thread info first
            cursor.execute("""
            SELECT employer_id, candidate_id FROM chat_threads WHERE id = %s
            """, (thread_id,))
            thread_info = cursor.fetchone()
            
            if not thread_info:
                return False
            
            # Update messages status
            update_messages = """
            UPDATE messages 
            SET status = 'seen' 
            WHERE thread_id = %s 
              AND receiver_id = %s 
              AND status IN ('sent', 'delivered')
            RETURNING COUNT(*) as updated_count
            """
            cursor.execute(update_messages, (thread_id, user_id))
            updated_count = cursor.fetchone()['updated_count']
            
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
                "unread_counts": unread_counts
            }
            await websocket_manager.broadcast_status_update(
                thread_id, user_id, "seen", status_data
            )
            
            logger.info(f"Messages marked as seen for user {user_id} in thread {thread_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking messages as seen: {e}")
            return False
    
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
            
            cursor.execute(insert_query, (
                thread_id,
                thread_data['application_id'],
                thread_data['job_id'],
                thread_data['employer_id'],
                thread_data['candidate_id'],
                thread_data.get('candidate_name'),
                thread_data.get('job_title')
            ))
            
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
            last_message = messages[0]['message_text'].lower()
            
            # Basic keyword matching for demo
            suggestions = []
            
            if any(word in last_message for word in ['halo', 'hello', 'hi', 'hey']):
                suggestions = [
                    "Halo! Ada yang bisa saya bantu?",
                    "Selamat pagi/siang/sore!",
                    "Halo, terima kasih telah menghubungi"
                ]
            elif any(word in last_message for word in ['interview', 'wawancara']):
                suggestions = [
                    "Kapan Anda available untuk interview?",
                    "Lokasi interview di kantor kami",
                    "Interview akan dilakukan via Zoom"
                ]
            elif any(word in last_message for word in ['terima kasih', 'thanks']):
                suggestions = [
                    "Sama-sama!",
                    "Terima kasih kembali",
                    "Dengan senang hati"
                ]
            elif any(word in last_message for word in ['gaji', 'salary', 'uang']):
                suggestions = [
                    "Range gaji untuk posisi ini adalah...",
                    "Bisa kita diskusikan lebih lanjut",
                    "Package termasuk benefits dan bonus"
                ]
            else:
                suggestions = [
                    "Bisa Anda jelaskan lebih detail?",
                    "Saya akan cek terlebih dahulu",
                    "Apakah ada pertanyaan lain?"
                ]
            
            return suggestions[:3]  # Return max 3 suggestions
            
        except Exception as e:
            logger.error(f"Error generating AI suggestions: {e}")
            return []