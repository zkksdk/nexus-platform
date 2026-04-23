from datetime import datetime
from pydantic import BaseModel


class FriendResponse(BaseModel):
    agent_id: str
    name: str
    avatar_url: str | None = None
    tier: str


class FriendListResponse(BaseModel):
    items: list[FriendResponse]
    total: int


class DirectMessageCreate(BaseModel):
    content: str


class DirectMessageResponse(BaseModel):
    message_id: int
    sender_agent_id: str
    recipient_agent_id: str
    content: str
    created_at: datetime


class DirectMessageListResponse(BaseModel):
    items: list[DirectMessageResponse]
    total: int
