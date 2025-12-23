from fastapi import WebSocket
from typing import Optional

from app.services.auth import verify_token, auth
from app.schemas.user import UserResponse


async def get_current_user_from_ws(websocket: WebSocket) -> Optional[UserResponse]:
    """
    Extract user from WebSocket connection.

    Expects a `token` query parameter containing the same JWT used
    for HTTP authentication.
    """
    token = websocket.query_params.get("token")
    if not token:
        return None

    try:
        token_data = verify_token(token)
        if not token_data:
            return None
        
        email = token_data.get("email")
        if not email:
            return None
        
        user_data = auth.get_user_by_email(email)
        if not user_data:
            return None
        
        return UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            username=user_data["username"],
            full_name=user_data.get("full_name"),
            is_active=user_data["is_active"],
            is_superuser=user_data.get("is_superuser", False),
            role=user_data["role"]
        )
    except Exception:
        return None


