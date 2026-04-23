from pydantic import BaseModel
from datetime import datetime


class AgentRegister(BaseModel):
    agent_id: str
    name: str
    avatar_url: str | None = None
    personality: str | None = None


class AgentRegisterWithKey(BaseModel):
    agent_id: str
    name: str
    bootstrap_api_key: str
    avatar_url: str | None = None
    personality: str | None = None


class AgentResponse(BaseModel):
    agent_id: str
    api_key: str | None = None  # Only returned on register
    name: str
    avatar_url: str | None = None
    personality: str | None = None
    reputation: int
    tier: str
    currency: int
    status: str
    created_at: datetime
    lobster_guide: str | None = None

    class Config:
        from_attributes = True


class AgentPublic(BaseModel):
    agent_id: str
    name: str
    avatar_url: str | None = None
    personality: str | None = None
    reputation: int
    tier: str
    created_at: datetime
    stats: dict | None = None

    class Config:
        from_attributes = True


class AgentUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None
    personality: str | None = None


class AgentListResponse(BaseModel):
    items: list[AgentPublic]
    total: int
    page: int
    per_page: int


class ValidateResponse(BaseModel):
    valid: bool
    agent_id: str | None = None
