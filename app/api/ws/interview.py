from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.interview_repository import InterviewRepository
from app.services.interview_service import InterviewRuntime
from app.services.security_ws import get_current_user_from_ws
from app.schemas.user import UserResponse


router = APIRouter()

repo = InterviewRepository()


@router.websocket(f"{settings.API_V1_PREFIX}/ws/interview/{{session_id}}")
async def interview_ws(
    websocket: WebSocket,
    session_id: int,
):
    # Must accept WebSocket connection first before we can do anything
    await websocket.accept()
    
    # Authenticate user from WebSocket (e.g. token query param)
    current_user = await get_current_user_from_ws(websocket)
    if current_user is None:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    # Create database session for WebSocket (can't use Depends)
    db: AsyncSession = SessionLocal()
    try:
        session = await repo.get_session(db, session_id=session_id)
        if not session or session.user_id != current_user.id or session.status != "active":
            await websocket.close(code=4404, reason="Session not found or not active")
            return

        runtime = InterviewRuntime(websocket=websocket, db=db, session=session, repo=repo)

        try:
            # Send intro + first question
            await runtime.start_interview()

            while True:
                data: Dict[str, Any] = await websocket.receive_json()
                event_type = data.get("type")
                payload = data.get("payload") or {}

                if event_type == "USER_TEXT_ANSWER":
                    await runtime.handle_text_answer(payload.get("message", ""))
                elif event_type == "USER_AUDIO_CHUNK":
                    await runtime.handle_audio_chunk(
                        payload.get("chunk"), is_first=payload.get("isFirst", False)
                    )
                elif event_type == "USER_AUDIO_END":
                    await runtime.handle_audio_end()
                elif event_type == "CONTROL_UPDATE":
                    await runtime.handle_control_update(payload)
                elif event_type == "HANGUP":
                    await runtime.handle_hangup()
                    break
        except WebSocketDisconnect:
            await runtime.handle_disconnect()
        except Exception as exc:  # pragma: no cover - defensive
            await runtime.send_error(str(exc))
            await websocket.close()
    finally:
        await db.close()


