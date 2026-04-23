from datetime import datetime
from pydantic import BaseModel


class MessageResponse(BaseModel):
    message_id: int
    message_type: str
    content: str
    is_read: bool
    created_at: datetime
    sender: dict
    topic_ref: dict | None = None


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
