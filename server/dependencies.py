from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from server.db.database import get_db
from server.models import Agent

# Map of api_key -> agent_id (in-memory for now, can move to Redis)
_api_key_cache: dict[str, int] = {}


def get_api_key_cache() -> dict:
    return _api_key_cache


async def get_current_agent(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Agent:
    """Authenticate request using X-API-Key header."""
    agent = db.query(Agent).filter(Agent.api_key == x_api_key).first()
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return agent
