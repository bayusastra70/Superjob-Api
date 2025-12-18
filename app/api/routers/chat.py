from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request
from typing import List, Optional
import logging

from app.services.websocket_manager import websocket_manager
from datetime import datetime

from app.schemas.chat import (
    MessageCreate,
    MessageResponse,
    ChatThreadResponse,
    ChatListResponse,
    ThreadCreate,
    AISuggestionRequest,
    AISuggestionResponse,
)
from app.services.chat_service import ChatService
from app.core.security import get_current_user
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat & Messaging"])

chat_service = ChatService()

@router.get("/websocket-info")
async def get_websocket_info(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get WebSocket connection URL with token and real-time status"""
    
    # 1. Get token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
    
    # 2. Get base URL from request
    base_url = str(request.base_url).replace("http", "ws").rstrip("/")
    
    # 3. Build WebSocket URLs
    websocket_url = f"{base_url}/api/v1/ws/chat"
    websocket_thread_url = f"{base_url}/api/v1/ws/chat/{{thread_id}}"
    
    if token:
        websocket_url += f"?token={token}"
        websocket_thread_url += f"?token={token}"
    
    # 4. Get REAL-TIME status from websocket_manager AS-IS
    ws_status = {
        # Basic counts
        "total_connected_users": len(websocket_manager.active_connections),
        "total_subscribed_threads": len(websocket_manager.thread_subscriptions),
        "total_activity_subscriptions": len(websocket_manager.activity_subscriptions),
        
        # Current user status
        "current_user_connected": current_user.id in websocket_manager.active_connections,
        "current_user_thread_subscriptions": [],
        "current_user_activity_subscriptions": [],
        
        # System overview (mask sensitive info)
        "connected_user_ids": list(websocket_manager.active_connections.keys()),
        "active_thread_ids": list(websocket_manager.thread_subscriptions.keys()),
        "activity_subscription_keys": list(websocket_manager.activity_subscriptions.keys()),
    }
    
    # 5. Check user's specific subscriptions
    # Thread subscriptions
    for thread_id, users in websocket_manager.thread_subscriptions.items():
        if current_user.id in users:
            ws_status["current_user_thread_subscriptions"].append({
                "thread_id": thread_id,
                "total_subscribers": len(users)
            })
    
    # Activity subscriptions  
    for employer_id, users in websocket_manager.activity_subscriptions.items():
        if current_user.id in users:
            ws_status["current_user_activity_subscriptions"].append({
                "employer_id": employer_id,
                "total_subscribers": len(users)
            })
    
    # 6. Get subscription stats per thread
    thread_stats = []
    for thread_id, users in websocket_manager.thread_subscriptions.items():
        thread_stats.append({
            "thread_id": thread_id,
            "subscriber_count": len(users),
            "subscriber_ids": list(users)
        })
    
    # 7. Get activity subscription stats
    activity_stats = []
    for employer_id, users in websocket_manager.activity_subscriptions.items():
        activity_stats.append({
            "employer_id": employer_id,
            "subscriber_count": len(users),
            "subscriber_ids": list(users)
        })
    
    return {
        # Connection URLs
        "websocket_url": websocket_url,
        "websocket_thread_url": websocket_thread_url,
        "base_url": base_url,
        
        # User info
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "token_present": bool(token),
            "token_preview": token[:20] + "..." if token else None
        },
        
        # Real-time WebSocket system status
        "websocket_system": {
            "status_summary": ws_status,
            "detailed_stats": {
                "thread_subscriptions": thread_stats,
                "activity_subscriptions": activity_stats
            },
            "monitoring": {
                "connected_users_count": ws_status["total_connected_users"],
                "active_threads_count": ws_status["total_subscribed_threads"],
                "activity_feeds_count": ws_status["total_activity_subscriptions"],
                "server_time": datetime.now().isoformat()
            }
        },
        
        # Diagnostic info
        "diagnostics": {
            "auth_header_received": auth_header[:50] + "..." if len(auth_header) > 50 else auth_header,
            "request_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }
    }

# Helper function untuk menentukan user type
def get_user_type(user: UserResponse, thread_id: str = None) -> str:
    """Determine if user is employer or candidate"""

    # if "admin" in user.email or "manager" in user.email:
    #     return "employer"

    if "admin" in user.role or "employer" in user.role:
        return "employer"
    return "candidate"


@router.get(
    "/list",
    response_model=ChatListResponse,
    summary="Get Chat List",
    description="""
    Mendapatkan daftar chat threads untuk user yang sedang login.
    
    Response berisi semua thread chat beserta total unread messages.
    
    **Test Data:**
    - Login sebagai `employer@superjob.com` untuk melihat chat threads
    - Login sebagai `candidate@superjob.com` untuk melihat chat dari sisi candidate
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
async def get_chat_list(current_user: UserResponse = Depends(get_current_user)):
    """Get list of chat threads for current user"""
    try:
        logger.info(f"CURRENT USER => {current_user}")
        user_type = get_user_type(current_user)
        logger.info(f"USER TYPE => {user_type}")
        threads = chat_service.get_chat_threads(current_user.id, user_type)

        # Calculate total unread
        total_unread = 0
        if user_type == "employer":
            total_unread = sum(t["unread_count_employer"] for t in threads)
        else:
            total_unread = sum(t["unread_count_candidate"] for t in threads)

        return ChatListResponse(threads=threads, total_unread=total_unread)

    except Exception as e:
        logger.error(f"Error getting chat list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{thread_id}", response_model=List[MessageResponse])
async def get_chat_history(
    thread_id: str,
    limit: int = Query(100, ge=1, le=500),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get chat history for a thread"""
    try:
        messages = chat_service.get_thread_messages(thread_id, limit)

        if not messages:
            raise HTTPException(
                status_code=404, detail="Thread not found or no messages"
            )

        return messages

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{thread_id}/messages")
# async def send_message(
#     request: Request,
#     thread_id: str,
#     message_data: MessageCreate,
#     current_user: UserResponse = Depends(get_current_user)
# ):
#     """Send a new message"""
#     try:
#         # Validate thread_id matches
#         if message_data.thread_id != thread_id:
#             raise HTTPException(status_code=400, detail="Thread ID mismatch")

#         # Send message
#         message_id = await chat_service.send_message(
#             sender_id=current_user.id,
#             sender_name=current_user.full_name or current_user.username,
#             message_data=message_data,
#             sender_role=getattr(current_user, "role", None),
#             ip_address=request.client.host,
#             user_agent=request.headers.get("user-agent"),
#         )

#         if not message_id:
#             raise HTTPException(status_code=404, detail="Thread not found")

#         return {
#             "message": "Message sent successfully",
#             "message_id": message_id,
#             "thread_id": thread_id
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error sending message: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


@router.post("/{thread_id}/messages")
async def send_message(
    thread_id: str,
    message_data: MessageCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Send a new message"""
    try:
        # Validate thread_id matches
        if message_data.thread_id != thread_id:
            raise HTTPException(status_code=400, detail="Thread ID mismatch")

        # Send message - HANYA kirim 3 parameter yang diperlukan
        result = await chat_service.send_message(
            sender_id=str(current_user.id),  # Pastikan string
            sender_name=current_user.full_name or current_user.username,
            message_data=message_data,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Thread not found")

        return {
            "message": "Message sent successfully",
            "message_id": result.get("message_id"),
            "thread_id": thread_id,
            "receiver_id": result.get("receiver_id"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/threads/create")
async def create_chat_thread(
    thread_data: ThreadCreate, current_user: UserResponse = Depends(get_current_user)
):
    """Create a new chat thread"""
    try:
        thread_id = chat_service.create_thread(thread_data.dict())

        if not thread_id:
            raise HTTPException(status_code=400, detail="Failed to create thread")

        return {"message": "Chat thread created successfully", "thread_id": thread_id}

    except Exception as e:
        logger.error(f"Error creating chat thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{thread_id}/read")
async def mark_as_read(
    thread_id: str, current_user: UserResponse = Depends(get_current_user)
):
    """Mark all messages as read in a thread"""
    try:
        # mark_messages_as_seen adalah async function, jadi harus di-await
        success = await chat_service.mark_messages_as_seen(thread_id, current_user.id)

        if not success:
            raise HTTPException(status_code=404, detail="Thread not found")

        return {"message": "Messages marked as read", "thread_id": thread_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking messages as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{thread_id}/ai-suggestions", response_model=AISuggestionResponse)
async def get_ai_suggestions(
    thread_id: str,
    request: AISuggestionRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get AI reply suggestions for a chat"""
    logger.info("TEST AI");
    try:
        suggestions = chat_service.get_ai_suggestions(thread_id, request.limit)

        context_valid = (
            len(suggestions) > 0 and suggestions[0] != "Tidak ada saran balasan"
        )

        return AISuggestionResponse(
            suggestions=suggestions, context_valid=context_valid
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
        thread_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM messages")
        message_count = cursor.fetchone()["count"]

        return {
            "status": "Chat system ready",
            "threads_count": thread_count,
            "messages_count": message_count,
            "endpoints": {
                "GET /chat/list": "Get chat list",
                "GET /chat/{thread_id}": "Get chat history",
                "POST /chat/{thread_id}/messages": "Send message",
                "PATCH /chat/{thread_id}/read": "Mark as read",
                "POST /chat/{thread_id}/ai-suggestions": "Get AI suggestions",
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
