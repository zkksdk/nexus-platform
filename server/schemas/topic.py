from pydantic import BaseModel
from datetime import datetime


class TopicCreate(BaseModel):
    title: str
    body: str
    tags: list[str] = []
    discussion_type: str = "linear"
    source_url: str | None = None


class TopicResponse(BaseModel):
    topic_id: str
    author: dict
    title: str
    body: str
    tags: list[str] = []
    discussion_type: str
    status: str
    quality_tier: str
    score: int
    view_count: int
    comment_count: int
    source_url: str | None
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopicUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    status: str | None = None
    tags: list[str] | None = None


class TopicListResponse(BaseModel):
    items: list[TopicResponse]
    total: int
    page: int
    per_page: int
