import asyncio
import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Store active connections: user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}
        # Store user subscriptions: thread_id -> set of user_ids
        self.thread_subscriptions: Dict[str, Set[int]] = {}
        # Store activity subscribers: employer_id -> set of user_ids
        self.activity_subscriptions: Dict[str, Set[int]] = {}

        self.user_last_activity: Dict[int, float] = {}
        self.connection_metadata: Dict[int, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept WebSocket connection for a user"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "message": "Connected to chat server",
            "user_id": user_id
        }, user_id)

    # async def connect(self, websocket: WebSocket, user_id: int):
    #     """Accept WebSocket connection for a user"""
    #     await websocket.accept()
    #     self.active_connections[user_id] = websocket
    #     self.user_last_activity[user_id] = asyncio.get_event_loop().time()
    #     self.connection_metadata[user_id] = {
    #         "connected_at": asyncio.get_event_loop().time(),
    #         "ip": websocket.client.host if websocket.client else None,
    #         "user_agent": websocket.headers.get("user-agent")
    #     }
        
    #     logger.info(f"User {user_id} connected via WebSocket")
        
    #     # Send welcome message
    #     await self.send_personal_message({
    #         "type": "connection",
    #         "message": "Connected to chat server",
    #         "user_id": user_id,
    #         "server_time": datetime.now().isoformat(),
    #         "connection_id": str(uuid.uuid4())
    #     }, user_id)
    
    def disconnect(self, user_id: int):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            
            # Remove from all thread subscriptions
            for thread_id in list(self.thread_subscriptions.keys()):
                if user_id in self.thread_subscriptions[thread_id]:
                    self.thread_subscriptions[thread_id].remove(user_id)
            
            logger.info(f"User {user_id} disconnected")
    
    def subscribe_to_thread(self, thread_id: str, user_id: int):
        """Subscribe user to a chat thread"""
        if thread_id not in self.thread_subscriptions:
            self.thread_subscriptions[thread_id] = set()
        self.thread_subscriptions[thread_id].add(user_id)
        logger.info(f"User {user_id} subscribed to thread {thread_id}")
    
    def unsubscribe_from_thread(self, thread_id: str, user_id: int):
        """Unsubscribe user from a chat thread"""
        if thread_id in self.thread_subscriptions and user_id in self.thread_subscriptions[thread_id]:
            self.thread_subscriptions[thread_id].remove(user_id)
            logger.info(f"User {user_id} unsubscribed from thread {thread_id}")

    def subscribe_to_activities(self, employer_id: str, user_id: int):
        """Subscribe user to activity feed for employer"""
        key = str(employer_id)
        if key not in self.activity_subscriptions:
            self.activity_subscriptions[key] = set()
        self.activity_subscriptions[key].add(user_id)
        logger.info(f"User {user_id} subscribed to activities {key}")

    def unsubscribe_from_activities(self, employer_id: str, user_id: int):
        """Unsubscribe user from activity feed for employer"""
        key = str(employer_id)
        if key in self.activity_subscriptions and user_id in self.activity_subscriptions[key]:
            self.activity_subscriptions[key].remove(user_id)
            logger.info(f"User {user_id} unsubscribed from activities {key}")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: int):
        """Send message to a specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    # async def broadcast_to_thread(self, thread_id: str, message: Dict[str, Any], exclude_user: int = None):
    #     """Broadcast message to all users subscribed to a thread"""
    #     if thread_id in self.thread_subscriptions:
    #         for user_id in self.thread_subscriptions[thread_id].copy():
    #             if user_id != exclude_user and user_id in self.active_connections:
    #                 try:
    #                     await self.active_connections[user_id].send_json(message)
    #                 except Exception as e:
    #                     logger.error(f"Error broadcasting to user {user_id}: {e}")
    #                     self.disconnect(user_id)

    async def broadcast_to_thread(self, thread_id: str, message: Dict[str, Any], exclude_user: int = None):
        """Broadcast message to all users subscribed to a thread"""
        if thread_id in self.thread_subscriptions:
            disconnected_users = []
            
            for user_id in self.thread_subscriptions[thread_id].copy():
                # Skip excluded user
                if exclude_user is not None and user_id == exclude_user:
                    continue
                    
                if user_id in self.active_connections:
                    try:
                        await self.active_connections[user_id].send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to user {user_id}: {e}")
                        disconnected_users.append(user_id)
                        # Jangan disconnect di sini, biarkan ping/pong handle
                else:
                    # User tidak connected, tapi masih subscribed
                    disconnected_users.append(user_id)
            
            # Cleanup disconnected users dari subscription
            for user_id in disconnected_users:
                self.unsubscribe_from_thread(thread_id, user_id)

    async def broadcast_activity(self, employer_id: str, message: Dict[str, Any], exclude_user: int = None):
        """Broadcast activity updates to subscribers of an employer."""
        key = str(employer_id)
        if key in self.activity_subscriptions:
            for user_id in self.activity_subscriptions[key].copy():
                if exclude_user is not None and user_id == exclude_user:
                    continue
                if user_id in self.active_connections:
                    try:
                        await self.active_connections[user_id].send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting activity to user {user_id}: {e}")
                        self.disconnect(user_id)
    
    async def broadcast_status_update(self, thread_id: str, user_id: int, status_type: str, data: Dict[str, Any]):
        """Broadcast message status update"""
        message = {
            "type": "message:status:update",
            "thread_id": thread_id,
            "user_id": user_id,
            "status_type": status_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast_to_thread(thread_id, message, exclude_user=user_id)
    
    async def broadcast_new_message(self, thread_id: str, message_data: Dict[str, Any], sender_id: int):
        """Broadcast new message to thread subscribers"""
        message = {
            "type": "message:new",
            "thread_id": thread_id,
            "sender_id": sender_id,
            "message": message_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast_to_thread(thread_id, message, exclude_user=sender_id)

    
    async def send_notification(self, user_id: str, notification_data: dict):
        """Send in-app notification via WebSocket"""
        try:
            if user_id in self.active_connections:
                websocket = self.active_connections[user_id]
                await websocket.send_json({
                    "type": "notification:new",
                    "notification": notification_data
                })
        except Exception as e:
            logger.error(f"Error sending notification via WebSocket: {e}")

    

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
