from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class MessageOut(BaseModel):
    id: str
    employer_id: int
    sender: Optional[str] = None
    subject: Optional[str] = None
    preview: Optional[str] = None
    created_at: Optional[datetime] = None
    is_read: Optional[bool] = None


class MessageList(BaseModel):
    items: List[MessageOut]
    total: int
