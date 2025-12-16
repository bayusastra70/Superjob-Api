from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.schemas.interview import (
    CreateSessionRequest,
    CreateSessionResponse,
    InterviewConfig,
    InterviewEvaluation,
    InterviewSessionDetailResponse,
    InterviewSessionResponse,
    InterviewMessageResponse,
)
from app.schemas.user import UserResponse
from app.core.security import get_current_user
from app.models.interview import InterviewSession
from app.services.interview_repository import InterviewRepository


router = APIRouter(prefix="/interview", tags=["interview"])

repo = InterviewRepository()


def _build_evaluation(session: InterviewSession) -> InterviewEvaluation | None:
    """Build evaluation response from session if available."""
    # Only include evaluation for ended sessions
    if session.status != "ended":
        return None
    return InterviewEvaluation(
        score=session.ai_score,
        feedback=session.ai_feedback,
        status=session.evaluation_status,  # type: ignore[arg-type]
    )


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    payload: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    session = await repo.create_session(
        db,
        user_id=current_user.id,
        position=payload.position,
        level=payload.level,
        total_questions=payload.totalQuestions,
        interview_type=payload.type,
    )
    return CreateSessionResponse(sessionId=session.id, status=session.status)  # type: ignore[arg-type]


@router.post("/sessions/{session_id}/end", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "ended":
        return
    await repo.end_session(db, session=session)


@router.get("/sessions", response_model=List[InterviewSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    sessions = await repo.list_sessions_for_user(db, user_id=current_user.id)
    return [
        InterviewSessionResponse(
            id=s.id,
            status=s.status,  # type: ignore[arg-type]
            startedAt=s.started_at,
            endedAt=s.ended_at,
            config=InterviewConfig(
                position=s.position,
                level=s.level,
                totalQuestions=s.total_questions,
                type=s.interview_type,
            ),
            evaluation=_build_evaluation(s),
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=InterviewSessionDetailResponse)
async def get_session_detail(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    session = await repo.get_session_with_messages(db, session_id=session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    # To avoid duplicate system messages (especially the AI introduction)
    # when combining REST-loaded history with WebSocket events, we filter
    # out intro/question messages for *active* sessions here. The live
    # WebSocket stream is the source of truth for those system messages
    # during an ongoing interview.
    messages = session.messages
    if session.status == "active":
        messages = [
            m
            for m in messages
            if m.message_type not in ("intro", "question")
        ]

    return InterviewSessionDetailResponse(
        id=session.id,
        status=session.status,  # type: ignore[arg-type]
        startedAt=session.started_at,
        endedAt=session.ended_at,
        config=InterviewConfig(
            position=session.position,
            level=session.level,
            totalQuestions=session.total_questions,
            type=session.interview_type,
        ),
        evaluation=_build_evaluation(session),
        messages=[
            InterviewMessageResponse(
                id=m.id,
                sender=m.sender,
                content=m.content,
                message_type=m.message_type,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.get("/history/{session_id}", response_model=InterviewSessionDetailResponse)
async def get_interview_history(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get complete interview history detail for post-interview review.

    Unlike the session detail endpoint, this returns all messages without filtering,
    making it suitable for viewing past completed interviews.
    """
    session = await repo.get_session_with_messages(db, session_id=session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    return InterviewSessionDetailResponse(
        id=session.id,
        status=session.status,  # type: ignore[arg-type]
        startedAt=session.started_at,
        endedAt=session.ended_at,
        config=InterviewConfig(
            position=session.position,
            level=session.level,
            totalQuestions=session.total_questions,
            type=session.interview_type,
        ),
        evaluation=_build_evaluation(session),
        messages=[
            InterviewMessageResponse(
                id=m.id,
                sender=m.sender,
                content=m.content,
                message_type=m.message_type,
                created_at=m.created_at,
            )
            for m in session.messages
        ],
    )

