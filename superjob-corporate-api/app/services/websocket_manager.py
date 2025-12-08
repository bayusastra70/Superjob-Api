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
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: int):
        """Send message to a specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_thread(self, thread_id: str, message: Dict[str, Any], exclude_user: int = None):
        """Broadcast message to all users subscribed to a thread"""
        if thread_id in self.thread_subscriptions:
            for user_id in self.thread_subscriptions[thread_id].copy():
                if user_id != exclude_user and user_id in self.active_connections:
                    try:
                        await self.active_connections[user_id].send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to user {user_id}: {e}")
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

# Global WebSocket manager instance
websocket_manager = WebSocketManager()