from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    SEEN = "seen"
    FAILED = "failed"

class MessageCreate(BaseModel):
    thread_id: str
    receiver_id: int
    message_text: str
    is_ai_suggestion: Optional[int] = 0

class MessageResponse(BaseModel):
    id: str
    thread_id: str
    sender_id: int
    receiver_id: int
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None
    message_text: str
    status: MessageStatus
    is_ai_suggestion: int
    ai_suggestions: Optional[Dict[str, Any]] = None
    created_at: datetime

class ChatThreadResponse(BaseModel):
    id: str
    application_id: int
    job_id: int
    employer_id: int
    candidate_id: int
    employer_name: Optional[str] = None
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count_employer: int = 0
    unread_count_candidate: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

class ChatListResponse(BaseModel):
    threads: List[ChatThreadResponse]
    total_unread: int = 0

class ThreadCreate(BaseModel):
    application_id: int
    job_id: int
    employer_id: int
    candidate_id: int
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None

class AISuggestionRequest(BaseModel):
    thread_id: str
    limit: Optional[int] = 10

class AISuggestionResponse(BaseModel):
    suggestions: List[str]
    context_valid: bool = True