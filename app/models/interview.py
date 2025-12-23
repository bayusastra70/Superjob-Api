from datetime import datetime
from typing import List

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)

    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Session configuration
    position: Mapped[str] = mapped_column(String(255))
    level: Mapped[str] = mapped_column(String(50))
    total_questions: Mapped[int] = mapped_column(Integer)
    interview_type: Mapped[str] = mapped_column(String(50))

    # Flow tracking
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    current_question_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("interview_messages.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )

    # AI Evaluation results
    ai_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # "pending" | "processing" | "completed" | "failed"

    messages: Mapped[List["InterviewMessage"]] = relationship(
        "InterviewMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="InterviewMessage.created_at",
        foreign_keys="InterviewMessage.session_id",
    )


class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        index=True,
    )

    sender: Mapped[str] = mapped_column(String(10))  # "ai" | "user"
    role: Mapped[str] = mapped_column(String(20))  # "system" | "assistant" | "user"
    content: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(
        String(20)
    )  # "intro" | "question" | "answer" | "transcript" | "system" | "feedback"

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession",
        back_populates="messages",
        foreign_keys=[session_id],
    )
