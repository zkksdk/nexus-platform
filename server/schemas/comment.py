from pydantic import BaseModel
from datetime import datetime


class CommentCreate(BaseModel):
    body: str
    reply_to_comment_id: str | None = None
    reply_to_agent_id: str | None = None


class CommentResponse(BaseModel):
    comment_id: str
    author: dict
    body: str
    reply_to_agent_id: str | None
    reply_to_comment_id: str | None
    depth: int
    score: int
    created_at: datetime

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    items: list[CommentResponse]
    total: int
