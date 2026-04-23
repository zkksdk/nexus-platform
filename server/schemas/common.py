from pydantic import BaseModel
from datetime import datetime


class AgentRef(BaseModel):
    agent_id: str
    name: str
    avatar_url: str | None = None


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
