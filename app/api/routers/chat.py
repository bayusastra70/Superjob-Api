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


@router.get(
    "/websocket-info",
    summary="Get WebSocket Connection Info",
    description="""
    Mendapatkan informasi koneksi WebSocket dan status real-time sistem.
    
    **Tujuan:**
    Endpoint ini menyediakan URL WebSocket yang sudah include token,
    serta status real-time dari WebSocket system.
    
    **Data yang Dikembalikan:**
    
    **Connection URLs:**
    - `websocket_url`: URL untuk general chat WebSocket
    - `websocket_thread_url`: URL template untuk thread-specific WebSocket
    
    **User Info:**
    - `id`, `email`: Info user yang sedang login
    - `token_present`: Apakah token tersedia
    
    **WebSocket System Status:**
    - `total_connected_users`: Jumlah user yang terkoneksi
    - `total_subscribed_threads`: Jumlah thread dengan subscriber
    - `current_user_connected`: Apakah user ini terkoneksi via WebSocket
    - `current_user_thread_subscriptions`: Thread yang di-subscribe user
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Gunakan response ini untuk setup WebSocket connection di frontend.
    - URL sudah include token, tinggal connect.
    """,
    responses={
        200: {"description": "WebSocket info berhasil diambil"},
    },
)
async def get_websocket_info(
    request: Request, current_user: UserResponse = Depends(get_current_user)
):
    """
    Mendapatkan informasi koneksi WebSocket dan status real-time.

    Args:
        request: Request object untuk mendapatkan base URL dan headers.
        current_user: User yang sedang login.

    Returns:
        dict: WebSocket URLs, user info, dan system status.
    """

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
        "current_user_connected": current_user.id
        in websocket_manager.active_connections,
        "current_user_thread_subscriptions": [],
        "current_user_activity_subscriptions": [],
        # System overview (mask sensitive info)
        "connected_user_ids": list(websocket_manager.active_connections.keys()),
        "active_thread_ids": list(websocket_manager.thread_subscriptions.keys()),
        "activity_subscription_keys": list(
            websocket_manager.activity_subscriptions.keys()
        ),
    }

    # 5. Check user's specific subscriptions
    # Thread subscriptions
    for thread_id, users in websocket_manager.thread_subscriptions.items():
        if current_user.id in users:
            ws_status["current_user_thread_subscriptions"].append(
                {"thread_id": thread_id, "total_subscribers": len(users)}
            )

    # Activity subscriptions
    for employer_id, users in websocket_manager.activity_subscriptions.items():
        if current_user.id in users:
            ws_status["current_user_activity_subscriptions"].append(
                {"employer_id": employer_id, "total_subscribers": len(users)}
            )

    # 6. Get subscription stats per thread
    thread_stats = []
    for thread_id, users in websocket_manager.thread_subscriptions.items():
        thread_stats.append(
            {
                "thread_id": thread_id,
                "subscriber_count": len(users),
                "subscriber_ids": list(users),
            }
        )

    # 7. Get activity subscription stats
    activity_stats = []
    for employer_id, users in websocket_manager.activity_subscriptions.items():
        activity_stats.append(
            {
                "employer_id": employer_id,
                "subscriber_count": len(users),
                "subscriber_ids": list(users),
            }
        )

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
            "token_preview": token[:20] + "..." if token else None,
        },
        # Real-time WebSocket system status
        "websocket_system": {
            "status_summary": ws_status,
            "detailed_stats": {
                "thread_subscriptions": thread_stats,
                "activity_subscriptions": activity_stats,
            },
            "monitoring": {
                "connected_users_count": ws_status["total_connected_users"],
                "active_threads_count": ws_status["total_subscribed_threads"],
                "activity_feeds_count": ws_status["total_activity_subscriptions"],
                "server_time": datetime.utcnow().isoformat()
            }
        },
        # Diagnostic info
        "diagnostics": {
            "auth_header_received": auth_header[:50] + "..."
            if len(auth_header) > 50
            else auth_header,
            "request_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
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


@router.get(
    "/{thread_id}",
    response_model=List[MessageResponse],
    summary="Get Chat History",
    description="""
    Mendapatkan riwayat pesan dari thread tertentu.
    
    **Format thread_id:** String (contoh: `thread-123`)
    
    **Query Parameters:**
    - `limit`: Jumlah maksimal pesan (default: 100, max: 500)
    
    **Data yang Dikembalikan per Message:**
    - `id`: ID pesan
    - `thread_id`: ID thread
    - `sender_id`: ID pengirim
    - `sender_name`: Nama pengirim
    - `message_text`: Isi pesan
    - `is_ai_suggestion`: Apakah pesan dari AI
    - `created_at`: Waktu pesan dikirim
    - `is_read`: Status baca
    
    **Response:**
    - `200 OK`: Riwayat pesan berhasil diambil
    - `404 Not Found`: Thread tidak ditemukan atau tidak ada pesan
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Riwayat pesan berhasil diambil"},
        404: {"description": "Thread tidak ditemukan atau tidak ada pesan"},
        500: {"description": "Internal server error"},
    },
)
async def get_chat_history(
    thread_id: str = Path(
        ...,
        description="ID thread chat",
        example="thread-123",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Jumlah maksimal pesan yang dikembalikan",
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Mendapatkan riwayat pesan dari thread tertentu.

    Args:
        thread_id: ID thread chat.
        limit: Jumlah maksimal pesan.
        current_user: User yang sedang login.

    Returns:
        List[MessageResponse]: Daftar pesan dalam thread.

    Raises:
        HTTPException: 404 jika thread tidak ditemukan.
        HTTPException: 500 jika terjadi error.
    """
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


@router.post(
    "/{thread_id}/messages",
    summary="Send Message",
    description="""
    Mengirim pesan baru ke thread chat.
    
    **Format thread_id:** String (contoh: `thread-123`)
    
    **Request Body:**
    - `thread_id` (required): ID thread (harus sama dengan path)
    - `receiver_id` (required): ID penerima pesan
    - `message_text` (required): Isi pesan
    - `is_ai_suggestion` (optional): 1 jika pesan dari AI, 0 jika bukan
    
    **Contoh Request Body:**
    ```json
    {
        "thread_id": "thread-123",
        "receiver_id": 5,
        "message_text": "Halo, apakah posisi masih tersedia?",
        "is_ai_suggestion": 0
    }
    ```
    
    **Response:**
    - `200 OK`: Pesan berhasil dikirim
    - `400 Bad Request`: Thread ID mismatch
    - `404 Not Found`: Thread tidak ditemukan
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Pesan akan di-broadcast via WebSocket ke semua subscriber.
    """,
    responses={
        200: {"description": "Pesan berhasil dikirim"},
        400: {"description": "Thread ID mismatch"},
        404: {"description": "Thread tidak ditemukan"},
        500: {"description": "Internal server error"},
    },
)
async def send_message(
    thread_id: str = Path(
        ...,
        description="ID thread chat",
        example="thread-123",
    ),
    message_data: MessageCreate = ...,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Mengirim pesan baru ke thread chat.

    Args:
        thread_id: ID thread tujuan.
        message_data: Data pesan yang akan dikirim.
        current_user: User yang mengirim pesan.

    Returns:
        dict: Message sukses dengan message_id dan thread_id.

    Raises:
        HTTPException: 400 jika thread_id mismatch.
        HTTPException: 404 jika thread tidak ditemukan.
        HTTPException: 500 jika terjadi error.
    """
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


@router.post(
    "/threads/create",
    summary="Create Chat Thread",
    description="""
    Membuat thread chat baru.
    
    **Request Body:**
    - `employer_id` (required): ID employer
    - `candidate_id` (required): ID candidate
    - `job_id` (optional): ID lowongan terkait
    - `subject` (optional): Subjek/judul chat
    
    **Contoh Request Body:**
    ```json
    {
        "employer_id": 8,
        "candidate_id": 5,
        "job_id": 1,
        "subject": "Diskusi Posisi Software Engineer"
    }
    ```
    
    **Response:**
    - `200 OK`: Thread berhasil dibuat
    - `400 Bad Request`: Gagal membuat thread
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Thread berhasil dibuat"},
        400: {"description": "Gagal membuat thread"},
        500: {"description": "Internal server error"},
    },
)
async def create_chat_thread(
    thread_data: ThreadCreate, current_user: UserResponse = Depends(get_current_user)
):
    """
    Membuat thread chat baru.

    Args:
        thread_data: Data thread yang akan dibuat.
        current_user: User yang membuat thread.

    Returns:
        dict: Message sukses dengan thread_id.

    Raises:
        HTTPException: 400 jika gagal membuat thread.
        HTTPException: 500 jika terjadi error.
    """
    try:
        thread_id = chat_service.create_thread(thread_data.dict())

        if not thread_id:
            raise HTTPException(status_code=400, detail="Failed to create thread")

        return {"message": "Chat thread created successfully", "thread_id": thread_id}

    except Exception as e:
        logger.error(f"Error creating chat thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/{thread_id}/read",
    summary="Mark Messages as Read",
    description="""
    Menandai semua pesan dalam thread sebagai sudah dibaca.
    
    **Format thread_id:** String (contoh: `thread-123`)
    
    **Response:**
    - `200 OK`: Pesan berhasil ditandai sebagai dibaca
    - `404 Not Found`: Thread tidak ditemukan
    
    **⚠️ Membutuhkan Authorization Token!**
    
    **Catatan:**
    - Menandai semua pesan yang diterima oleh user sebagai read.
    - Berguna untuk reset unread count di UI.
    """,
    responses={
        200: {"description": "Pesan berhasil ditandai sebagai dibaca"},
        404: {"description": "Thread tidak ditemukan"},
        500: {"description": "Internal server error"},
    },
)
async def mark_as_read(
    thread_id: str = Path(
        ...,
        description="ID thread chat",
        example="thread-123",
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Menandai semua pesan dalam thread sebagai sudah dibaca.

    Args:
        thread_id: ID thread chat.
        current_user: User yang menandai pesan.

    Returns:
        dict: Message sukses dengan thread_id.

    Raises:
        HTTPException: 404 jika thread tidak ditemukan.
        HTTPException: 500 jika terjadi error.
    """
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


@router.post(
    "/{thread_id}/ai-suggestions",
    response_model=AISuggestionResponse,
    summary="Get AI Reply Suggestions",
    description="""
    Mendapatkan saran balasan dari AI untuk thread chat.
    
    **Format thread_id:** String (contoh: `thread-123`)
    
    **Tujuan:**
    Endpoint ini menggunakan AI untuk menganalisis konteks percakapan
    dan memberikan saran balasan yang relevan.
    
    **Request Body:**
    - `limit` (optional): Jumlah saran yang diminta (default: 3)
    
    **Contoh Request Body:**
    ```json
    {
        "limit": 3
    }
    ```
    
    **Response:**
    - `suggestions`: Array saran balasan dari AI
    - `context_valid`: Boolean apakah konteks valid untuk saran
    
    **Contoh Response:**
    ```json
    {
        "suggestions": [
            "Terima kasih atas informasinya. Kapan saya bisa mulai interview?",
            "Baik, saya akan menyiapkan dokumen yang diperlukan.",
            "Apakah ada hal lain yang perlu saya persiapkan?"
        ],
        "context_valid": true
    }
    ```
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
    responses={
        200: {"description": "Saran AI berhasil diambil"},
        500: {"description": "Gagal mendapatkan saran AI"},
    },
)
async def get_ai_suggestions(
    thread_id: str = Path(
        ...,
        description="ID thread chat",
        example="thread-123",
    ),
    request: AISuggestionRequest = ...,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Mendapatkan saran balasan dari AI untuk thread chat.

    Args:
        thread_id: ID thread chat.
        request: Request dengan limit saran.
        current_user: User yang meminta saran.

    Returns:
        AISuggestionResponse: Daftar saran balasan dari AI.

    Raises:
        HTTPException: 500 jika gagal mendapatkan saran.
    """
    logger.info("TEST AI")
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


@router.get(
    "/test/sample",
    summary="Test Chat System",
    description="""
    Endpoint test untuk memverifikasi setup sistem chat.
    
    **Tujuan:**
    Endpoint ini digunakan untuk debugging dan memastikan
    sistem chat sudah siap digunakan.
    
    **Data yang Dikembalikan:**
    - `status`: Status sistem
    - `threads_count`: Jumlah thread chat di database
    - `messages_count`: Jumlah pesan di database
    - `endpoints`: Daftar endpoint chat yang tersedia
    
    **Catatan:**
    - Endpoint ini tidak memerlukan authentication.
    - Sebaiknya di-disable di production untuk keamanan.
    """,
    responses={
        200: {"description": "Info sistem chat berhasil diambil"},
        500: {"description": "Internal server error"},
    },
)
async def test_sample_chat():
    """
    Test endpoint untuk memverifikasi setup sistem chat.

    Returns:
        dict: Status sistem dan statistik chat.

    Raises:
        HTTPException: 500 jika terjadi error.
    """
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
