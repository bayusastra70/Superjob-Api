"""
WebSocket Activity Router
=========================

Module ini menyediakan WebSocket endpoint untuk real-time activity updates.

**Endpoint:**
- `ws://host/ws/activities` - WebSocket untuk menerima activity updates

**Authentication:**
- Token JWT diperlukan melalui query parameter `token` atau header `Authorization: Bearer <token>`

**Message Types (Client → Server):**
- `subscribe`: Subscribe ke activities employer tertentu
- `unsubscribe`: Unsubscribe dari activities employer
- `ping`: Heartbeat untuk menjaga koneksi

**Message Types (Server → Client):**
- `activities:subscription`: Konfirmasi subscription status
- `pong`: Response untuk ping
- `error`: Error message
- `activity:new`: Activity baru (reminder, applicant, message, dll)

**Contoh Penggunaan:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/activities?token=JWT_TOKEN');

// Subscribe ke employer
ws.send(JSON.stringify({ type: 'subscribe', employer_id: '8' }));

// Heartbeat
ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));

// Listen for messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Activity:', data);
};
```
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.auth import verify_token
from app.services.websocket_manager import websocket_manager
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["WebSocket"])


async def get_current_user_from_token(token: str) -> Optional[UserResponse]:
    """
    Mengambil user dari JWT token.

    Fungsi ini memverifikasi token JWT dan mengambil data user
    dari database berdasarkan email yang ada di token payload.

    Args:
        token: JWT token string yang akan diverifikasi.

    Returns:
        UserResponse: Object user jika token valid dan user ditemukan.
        None: Jika token invalid atau user tidak ditemukan.

    Note:
        Fungsi ini tidak raise exception, melainkan return None
        untuk memudahkan penanganan di WebSocket handler.
    """
    try:
        token_data = verify_token(token)
        if not token_data:
            return None
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
            is_superuser=user_data.get("is_superuser", False),
        )
    except Exception as exc:
        logger.error("Error getting user from token", exc_info=exc)
        return None


@router.websocket("/activities")
async def websocket_activity_endpoint(
    websocket: WebSocket, token: Optional[str] = None, employer_id: Optional[str] = None
):
    """
    WebSocket endpoint untuk real-time activity updates.

    Endpoint ini memungkinkan client untuk menerima notifikasi real-time
    tentang aktivitas terbaru seperti reminder baru, pelamar baru,
    pesan baru, dan lainnya.

    **URL:** `ws://host/ws/activities`

    **Query Parameters:**
    - `token` (optional): JWT token untuk authentication.
      Alternatif: kirim via header `Authorization: Bearer <token>`
    - `employer_id` (optional): ID employer untuk langsung subscribe
      saat koneksi dibuat.

    **Client → Server Messages:**

    1. **Subscribe ke employer activities:**
    ```json
    {"type": "subscribe", "employer_id": "8"}
    ```
    Response: `{"type": "activities:subscription", "employer_id": "8", "status": "subscribed"}`

    2. **Unsubscribe dari employer activities:**
    ```json
    {"type": "unsubscribe", "employer_id": "8"}
    ```
    Response: `{"type": "activities:subscription", "employer_id": "8", "status": "unsubscribed"}`

    3. **Ping (heartbeat):**
    ```json
    {"type": "ping", "timestamp": 1702900000000}
    ```
    Response: `{"type": "pong", "timestamp": 1702900000000}`

    **Server → Client Messages:**

    - `activities:subscription`: Konfirmasi subscribe/unsubscribe
    - `pong`: Response untuk ping heartbeat
    - `error`: Error message (contoh: `{"type": "error", "message": "Invalid JSON"}`)
    - Activity events: Reminder, applicant, message updates

    **Error Codes:**
    - `1008`: Authentication required (token tidak valid)

    Args:
        websocket: WebSocket connection object.
        token: JWT token untuk authentication (query param).
        employer_id: ID employer untuk auto-subscribe saat connect.

    Note:
        - Koneksi akan ditutup dengan code 1008 jika authentication gagal.
        - Client sebaiknya implement reconnection logic dengan exponential backoff.
        - Ping setiap 30 detik direkomendasikan untuk menjaga koneksi.
    """
    user = None

    # Token dari query atau header Authorization: Bearer
    if not token:
        try:
            token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        except Exception:
            pass

    if token:
        user = await get_current_user_from_token(token)

    if not user:
        await websocket.close(code=1008, reason="Authentication required")
        return

    await websocket_manager.connect(websocket, user.id)

    if employer_id:
        websocket_manager.subscribe_to_activities(str(employer_id), user.id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
                message_type = message.get("type")
                if message_type == "subscribe":
                    emp_id = message.get("employer_id")
                    if emp_id:
                        websocket_manager.subscribe_to_activities(str(emp_id), user.id)
                        await websocket_manager.send_personal_message(
                            {
                                "type": "activities:subscription",
                                "employer_id": str(emp_id),
                                "status": "subscribed",
                            },
                            user.id,
                        )
                elif message_type == "unsubscribe":
                    emp_id = message.get("employer_id")
                    if emp_id:
                        websocket_manager.unsubscribe_from_activities(
                            str(emp_id), user.id
                        )
                        await websocket_manager.send_personal_message(
                            {
                                "type": "activities:subscription",
                                "employer_id": str(emp_id),
                                "status": "unsubscribed",
                            },
                            user.id,
                        )
                elif message_type == "ping":
                    await websocket_manager.send_personal_message(
                        {"type": "pong", "timestamp": message.get("timestamp")}, user.id
                    )
            except json.JSONDecodeError:
                await websocket_manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON"}, user.id
                )
    except WebSocketDisconnect:
        websocket_manager.disconnect(user.id)
    except Exception as exc:
        logger.error("WebSocket error for activities", exc_info=exc)
        websocket_manager.disconnect(user.id)
