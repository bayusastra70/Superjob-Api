# app/services/notification_service.py
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from collections import deque
import uuid
import json

from app.services.database import get_db_connection
from app.schemas.notification import NotificationCreate

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.notification_queue = deque()
        self.max_queue_size = 1000
        self.is_processing = False
        
    def _get_db(self):
        return get_db_connection()
    
    async def add_to_queue(self, notification_data: Dict):
        """Add notification to queue for reliability"""
        try:
            if len(self.notification_queue) < self.max_queue_size:
                self.notification_queue.append(notification_data)
                logger.info(f"Notification added to queue: {notification_data}")
                
                # Start processing if not already running
                if not self.is_processing:
                    asyncio.create_task(self.process_queue())
                    
            else:
                logger.warning("Notification queue is full, dropping notification")
                
        except Exception as e:
            logger.error(f"Error adding to notification queue: {e}")
    
    async def process_queue(self):
        """Process notification queue"""
        if self.is_processing:
            return
            
        self.is_processing = True
        
        try:
            while self.notification_queue:
                notification_data = self.notification_queue.popleft()
                
                try:
                    # Save to database
                    await self.create_notification(notification_data)
                    
                    # Here you can also integrate with push notification services
                    # like Firebase Cloud Messaging (FCM), OneSignal, etc.
                    await self.send_push_notification(notification_data)
                    
                except Exception as e:
                    logger.error(f"Error processing notification: {e}")
                    # Re-add to queue if failed
                    self.notification_queue.appendleft(notification_data)
                    await asyncio.sleep(1)  # Wait before retry
                    
        finally:
            self.is_processing = False
    
    async def create_notification(self, notification_data: Dict) -> Optional[str]:
        """Save notification to database"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            
            notification_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO notifications 
                (id, user_id, title, message, notification_type, data, thread_id, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                notification_id,
                notification_data["user_id"],
                notification_data["title"],
                notification_data["message"],
                notification_data.get("notification_type", "message"),
                json.dumps(notification_data.get("data", {})),
                notification_data.get("thread_id"),
                False,
                datetime.utcnow()
            ))
            
            conn.commit()
            logger.info(f"Notification saved to DB: {notification_id}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Error saving notification to DB: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    async def send_push_notification(self, notification_data: Dict):
        """Send push notification (implement based on your push service)"""
        try:
            # Example: Firebase Cloud Messaging (FCM)
            # You'll need to install `firebase-admin` and set up FCM
            user_id = notification_data["user_id"]
            
            # Get user's device tokens from database
            conn = self._get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT device_token FROM user_devices 
                WHERE user_id = %s AND is_active = TRUE
            """, (user_id,))
            
            device_tokens = [row['device_token'] for row in cursor.fetchall()]
            conn.close()
            
            if device_tokens:
                # Send to FCM (example structure)
                # This is a placeholder - implement based on your chosen service
                message = {
                    'notification': {
                        'title': notification_data["title"],
                        'body': notification_data["message"],
                    },
                    'data': notification_data.get("data", {}),
                    'tokens': device_tokens
                }
                
                # Uncomment and implement based on your push service
                # response = await fcm.send_multicast(message)
                # logger.info(f"Push notification sent: {response}")
                
                logger.info(f"Would send push to devices: {device_tokens}")
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
    
    async def get_user_notifications(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get notifications for a user"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM notifications 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, (user_id, limit, offset))
            
            notifications = cursor.fetchall()
            
            # Get total unread
            cursor.execute("""
                SELECT COUNT(*) as count FROM notifications 
                WHERE user_id = %s AND is_read = FALSE
            """, (user_id,))
            
            total_unread = cursor.fetchone()['count']
            conn.close()
            
            return {
                "notifications": notifications,
                "total_unread": total_unread
            }
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return {"notifications": [], "total_unread": 0}
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE notifications 
                SET is_read = TRUE 
                WHERE id = %s AND user_id = %s
            """, (notification_id, user_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    async def mark_all_as_read(self, user_id: str) -> bool:
        """Mark all notifications as read for a user"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE notifications 
                SET is_read = TRUE 
                WHERE user_id = %s AND is_read = FALSE
            """, (user_id,))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return False

# Singleton instance
notification_service = NotificationService()