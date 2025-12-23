from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


InterviewStatus = Literal["active", "ended"]
EvaluationStatus = Literal["pending", "processing", "completed", "failed"]


class InterviewConfig(BaseModel):
    position: str
    level: str
    totalQuestions: int
    type: str


class CreateSessionRequest(BaseModel):
    position: str
    level: str
    totalQuestions: int
    type: str


class CreateSessionResponse(BaseModel):
    sessionId: int
    status: InterviewStatus


class InterviewMessageResponse(BaseModel):
    id: int
    sender: Literal["ai", "user"]
    content: str
    message_type: Literal["intro", "question", "answer", "transcript", "system", "feedback"]
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewEvaluation(BaseModel):
    """AI evaluation results for an interview session."""
    score: Optional[int] = None
    feedback: Optional[str] = None
    status: EvaluationStatus

    class Config:
        from_attributes = True


class InterviewSessionResponse(BaseModel):
    id: int
    status: InterviewStatus
    startedAt: datetime
    endedAt: datetime | None
    config: InterviewConfig
    evaluation: Optional[InterviewEvaluation] = None

    class Config:
        from_attributes = True


class InterviewSessionDetailResponse(InterviewSessionResponse):
    messages: List[InterviewMessageResponse]


