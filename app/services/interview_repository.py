from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interview import InterviewMessage, InterviewSession


class InterviewRepository:
    async def create_session(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        position: str,
        level: str,
        total_questions: int,
        interview_type: str,
    ) -> InterviewSession:
        session = InterviewSession(
            user_id=user_id,
            position=position,
            level=level,
            total_questions=total_questions,
            interview_type=interview_type,
            question_count=total_questions,
            current_question_index=0,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def end_session(
        self, db: AsyncSession, *, session: InterviewSession
    ) -> InterviewSession:
        from datetime import datetime

        session.status = "ended"
        session.ended_at = datetime.utcnow()
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_session(
        self, db: AsyncSession, *, session_id: int
    ) -> Optional[InterviewSession]:
        result = await db.execute(
            select(InterviewSession).where(InterviewSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions_for_user(
        self, db: AsyncSession, *, user_id: int
    ) -> List[InterviewSession]:
        result = await db.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.started_at.desc())
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        db: AsyncSession,
        *,
        session: InterviewSession,
        sender: str,
        role: str,
        content: str,
        message_type: str,
    ) -> InterviewMessage:
        msg = InterviewMessage(
            session_id=session.id,
            sender=sender,
            role=role,
            content=content,
            message_type=message_type,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    async def get_message(
        self,
        db: AsyncSession,
        *,
        message_id: int,
    ) -> Optional[InterviewMessage]:
        """Fetch a message by its ID."""
        result = await db.execute(
            select(InterviewMessage).where(InterviewMessage.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_session_with_messages(
        self,
        db: AsyncSession,
        *,
        session_id: int,
    ) -> Optional[InterviewSession]:
        """Fetch a session with messages eagerly loaded to avoid async lazy-load issues."""
        result = await db.execute(
            select(InterviewSession)
            .options(selectinload(InterviewSession.messages))
            .where(InterviewSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def update_evaluation(
        self,
        db: AsyncSession,
        *,
        session_id: int,
        ai_score: Optional[int] = None,
        ai_feedback: Optional[str] = None,
        evaluation_status: str,
    ) -> Optional[InterviewSession]:
        """Update AI evaluation results for a session."""
        result = await db.execute(
            select(InterviewSession).where(InterviewSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            return None

        session.evaluation_status = evaluation_status
        if ai_score is not None:
            session.ai_score = ai_score
        if ai_feedback is not None:
            session.ai_feedback = ai_feedback

        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

