from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from app.schemas.chat import (
    MessageCreate, MessageResponse, ChatThreadResponse, 
    ChatListResponse, ThreadCreate, AISuggestionRequest, 
    AISuggestionResponse
)
from app.services.chat_service import ChatService
from app.core.security import get_current_user
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

chat_service = ChatService()

# Helper function untuk menentukan user type
def get_user_type(user: UserResponse, thread_id: str = None) -> str:
    """Determine if user is employer or candidate"""
    
    # if "admin" in user.email or "manager" in user.email:
    #     return "employer"

    if "admin" in user.role or "employer" in user.role:
        return "employer"
    return "candidate"

@router.get("/list", response_model=ChatListResponse)
async def get_chat_list(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get list of chat threads for current user"""
    try:
        logger.info(f"CURRENT USER => {current_user}" );
        user_type = get_user_type(current_user)
        logger.info(f"USER TYPE => {user_type}");
        threads = chat_service.get_chat_threads(current_user.id, user_type)
        
        # Calculate total unread
        total_unread = 0
        if user_type == "employer":
            total_unread = sum(t['unread_count_employer'] for t in threads)
        else:
            total_unread = sum(t['unread_count_candidate'] for t in threads)
        
        return ChatListResponse(
            threads=threads,
            total_unread=total_unread
        )
        
    except Exception as e:
        logger.error(f"Error getting chat list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{thread_id}", response_model=List[MessageResponse])
async def get_chat_history(
    thread_id: str,
    limit: int = Query(100, ge=1, le=500),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get chat history for a thread"""
    try:
        messages = chat_service.get_thread_messages(thread_id, limit)
        
        if not messages:
            raise HTTPException(status_code=404, detail="Thread not found or no messages")
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{thread_id}/messages")
async def send_message(
    thread_id: str,
    message_data: MessageCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Send a new message"""
    try:
        # Validate thread_id matches
        if message_data.thread_id != thread_id:
            raise HTTPException(status_code=400, detail="Thread ID mismatch")
        
        # Send message
        message_id = await chat_service.send_message(
            sender_id=current_user.id,
            sender_name=current_user.full_name or current_user.username,
            message_data=message_data
        )
        
        if not message_id:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return {
            "message": "Message sent successfully",
            "message_id": message_id,
            "thread_id": thread_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/threads/create")
async def create_chat_thread(
    thread_data: ThreadCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new chat thread"""
    try:
        thread_id = chat_service.create_thread(thread_data.dict())
        
        if not thread_id:
            raise HTTPException(status_code=400, detail="Failed to create thread")
        
        return {
            "message": "Chat thread created successfully",
            "thread_id": thread_id
        }
        
    except Exception as e:
        logger.error(f"Error creating chat thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{thread_id}/read")
async def mark_as_read(
    thread_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Mark all messages as read in a thread"""
    try:
        success = chat_service.mark_messages_as_seen(thread_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return {
            "message": "Messages marked as read",
            "thread_id": thread_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking messages as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{thread_id}/ai-suggestions", response_model=AISuggestionResponse)
async def get_ai_suggestions(
    thread_id: str,
    request: AISuggestionRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get AI reply suggestions for a chat"""
    try:
        suggestions = chat_service.get_ai_suggestions(thread_id, request.limit)
        
        context_valid = len(suggestions) > 0 and suggestions[0] != "Tidak ada saran balasan"
        
        return AISuggestionResponse(
            suggestions=suggestions,
            context_valid=context_valid
        )
        
    except Exception as e:
        logger.error(f"Error getting AI suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/sample")
async def test_sample_chat():
    """Test endpoint to verify chat setup"""
    try:
        from app.services.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM chat_threads")
        thread_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM messages")
        message_count = cursor.fetchone()['count']
        
        return {
            "status": "Chat system ready",
            "threads_count": thread_count,
            "messages_count": message_count,
            "endpoints": {
                "GET /chat/list": "Get chat list",
                "GET /chat/{thread_id}": "Get chat history",
                "POST /chat/{thread_id}/messages": "Send message",
                "PATCH /chat/{thread_id}/read": "Mark as read",
                "POST /chat/{thread_id}/ai-suggestions": "Get AI suggestions"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/websocket-info")
async def get_websocket_info(current_user: UserResponse = Depends(get_current_user)):
    """Get WebSocket connection information"""
    return {
        "websocket_url": f"ws://localhost:8000/api/v1/ws/chat?token=YOUR_TOKEN",
        "websocket_thread_url": f"ws://localhost:8000/api/v1/ws/chat/{{thread_id}}?token=YOUR_TOKEN",
        "events": {
            "message:new": "New message received",
            "message:status:update": "Message status updated (delivered → seen)",
            "typing": "User typing indicator",
            "subscription": "Subscription confirmation",
            "connection": "Connection established"
        },
        "client_messages": {
            "subscribe": '{"type": "subscribe", "thread_id": "thread_uuid"}',
            "unsubscribe": '{"type": "unsubscribe", "thread_id": "thread_uuid"}',
            "typing": '{"type": "typing", "thread_id": "thread_uuid", "is_typing": true/false}',
            "ping": '{"type": "ping", "timestamp": 1234567890}'
        }
    }