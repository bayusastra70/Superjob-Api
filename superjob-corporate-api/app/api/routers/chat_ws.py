from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import HTTPBearer
import json
import logging
from typing import Optional

from app.services.websocket_manager import websocket_manager
from app.services.auth import verify_token
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["WebSocket"])
security = HTTPBearer()

async def get_current_user_from_token(token: str) -> Optional[UserResponse]:
    """Get user from JWT token for WebSocket"""
    logger.info(f"Token get_current_user_from_token: {token}")
    try:
        token_data = verify_token(token)
        if not token_data:
            return None
        
        t = token_data.get("email");
        logger.info(f"Email Terbaca : {t}")
        from app.services.auth import auth
        user_data = auth.get_user_by_email(token_data.get("email"))
        
        if not user_data:
            return None
        
        return UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            username=user_data["username"],
            full_name=user_data.get("full_name"),
            is_active=user_data["is_active"],
            is_superuser=user_data.get("is_superuser", False)
        )
    except Exception as e:
        logger.error(f"Error getting user from token: {e}")
        return None

@router.websocket("/chat")
async def websocket_chat_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """WebSocket endpoint for real-time chat"""
    user = None
    
    # Try to get token from query params
    if not token:
        # Try to get from WebSocket headers/subprotocol
        try:
            token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        except:
            pass
    
    if token:
        user = await get_current_user_from_token(token)
    
    if not user:
        # Close connection if no valid token
        await websocket.close(code=1008, reason="Authentication required")
        return
    
    # Connect user
    await websocket_manager.connect(websocket, user.id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "subscribe":
                    # Subscribe to a thread
                    thread_id = message.get("thread_id")
                    if thread_id:
                        websocket_manager.subscribe_to_thread(thread_id, user.id)
                        
                        # Send confirmation
                        await websocket_manager.send_personal_message({
                            "type": "subscription",
                            "thread_id": thread_id,
                            "status": "subscribed"
                        }, user.id)
                
                elif message_type == "unsubscribe":
                    # Unsubscribe from a thread
                    thread_id = message.get("thread_id")
                    if thread_id:
                        websocket_manager.unsubscribe_from_thread(thread_id, user.id)
                        
                        # Send confirmation
                        await websocket_manager.send_personal_message({
                            "type": "subscription",
                            "thread_id": thread_id,
                            "status": "unsubscribed"
                        }, user.id)
                
                elif message_type == "typing":
                    # Broadcast typing indicator
                    thread_id = message.get("thread_id")
                    is_typing = message.get("is_typing", False)
                    
                    if thread_id:
                        await websocket_manager.broadcast_to_thread(
                            thread_id,
                            {
                                "type": "typing",
                                "thread_id": thread_id,
                                "user_id": user.id,
                                "is_typing": is_typing
                            },
                            exclude_user=user.id
                        )
                
                elif message_type == "ping":
                    # Respond to ping
                    await websocket_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }, user.id)
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket_manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, user.id)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id}")
        websocket_manager.disconnect(user.id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {e}")
        websocket_manager.disconnect(user.id)

@router.websocket("/chat/{thread_id}")
async def websocket_thread_endpoint(
    websocket: WebSocket, 
    thread_id: str,
    token: Optional[str] = None
):
    """WebSocket endpoint for specific chat thread"""
    user = None
    
    if not token:
        try:
            token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        except:
            pass
    
    if token:
        user = await get_current_user_from_token(token)
    
    if not user:
        await websocket.close(code=1008, reason="Authentication required")
        return
    
    # Connect user
    await websocket_manager.connect(websocket, user.id)
    
    # Auto-subscribe to this thread
    websocket_manager.subscribe_to_thread(thread_id, user.id)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "message":
                    # Handle direct message sending via WebSocket
                    message_text = message.get("text", "")
                    
                    if message_text:
                        from app.services.chat_service import ChatService
                        from app.schemas.chat import MessageCreate
                        
                        chat_service = ChatService()
                        
                        # Create message
                        message_data = MessageCreate(
                            thread_id=thread_id,
                            receiver_id=0,  # Will be determined by service
                            message_text=message_text,
                            is_ai_suggestion=0
                        )
                        
                        # Send message (will broadcast automatically)
                        await chat_service.send_message(
                            sender_id=user.id,
                            sender_name=user.full_name or user.username,
                            message_data=message_data
                        )
                
                elif message_type == "typing":
                    # Typing indicator
                    is_typing = message.get("is_typing", False)
                    await websocket_manager.broadcast_to_thread(
                        thread_id,
                        {
                            "type": "typing",
                            "thread_id": thread_id,
                            "user_id": user.id,
                            "is_typing": is_typing
                        },
                        exclude_user=user.id
                    )
                
                elif message_type == "read":
                    # Mark as read
                    from app.services.chat_service import ChatService
                    chat_service = ChatService()
                    await chat_service.mark_messages_as_seen(thread_id, user.id)
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket_manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, user.id)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id} from thread {thread_id}")
        websocket_manager.unsubscribe_from_thread(thread_id, user.id)
        websocket_manager.disconnect(user.id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.unsubscribe_from_thread(thread_id, user.id)
        websocket_manager.disconnect(user.id)