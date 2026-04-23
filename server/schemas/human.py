from datetime import datetime
from pydantic import BaseModel


class HumanKeyRequest(BaseModel):
    device_id: str
    device_meta: dict | None = None


class HumanKeyResponse(BaseModel):
    device_id: str
    agent_id: str
    api_key: str
    created_at: datetime
    next_allowed_at: datetime
    retry_after_seconds: int
    onboarding_prompt: str
    generated: bool
