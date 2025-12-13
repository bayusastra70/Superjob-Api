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
async def websocket_activity_endpoint(websocket: WebSocket, token: Optional[str] = None, employer_id: Optional[str] = None):
    """
    WebSocket untuk menerima activity updates.
    Client mengirim JSON: {"type": "subscribe", "employer_id": "..."}.
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
                            {"type": "activities:subscription", "employer_id": str(emp_id), "status": "subscribed"},
                            user.id,
                        )
                elif message_type == "unsubscribe":
                    emp_id = message.get("employer_id")
                    if emp_id:
                        websocket_manager.unsubscribe_from_activities(str(emp_id), user.id)
                        await websocket_manager.send_personal_message(
                            {"type": "activities:subscription", "employer_id": str(emp_id), "status": "unsubscribed"},
                            user.id,
                        )
                elif message_type == "ping":
                    await websocket_manager.send_personal_message({"type": "pong", "timestamp": message.get("timestamp")}, user.id)
            except json.JSONDecodeError:
                await websocket_manager.send_personal_message({"type": "error", "message": "Invalid JSON"}, user.id)
    except WebSocketDisconnect:
        websocket_manager.disconnect(user.id)
    except Exception as exc:
        logger.error("WebSocket error for activities", exc_info=exc)
        websocket_manager.disconnect(user.id)
