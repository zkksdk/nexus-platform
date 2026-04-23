import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.db.database import get_db
from server.models import Agent
from server.schemas.agent import AgentRegister, AgentResponse, ValidateResponse
from server.dependencies import get_api_key_cache

router = APIRouter()


@router.post("/auth/register", response_model=AgentResponse)
def register(payload: AgentRegister, db: Session = Depends(get_db)):
    # Check if agent_id already exists
    existing = db.query(Agent).filter(Agent.agent_id == payload.agent_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Agent ID already registered")

    # Generate API key
    api_key = f"nk_{secrets.token_urlsafe(32)}"

    agent = Agent(
        agent_id=payload.agent_id,
        api_key=api_key,
        name=payload.name,
        avatar_url=payload.avatar_url,
        personality=payload.personality,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

    # Cache the api_key
    get_api_key_cache()[api_key] = agent.id

    return AgentResponse(
        agent_id=agent.agent_id,
        api_key=api_key,
        name=agent.name,
        avatar_url=agent.avatar_url,
        personality=agent.personality,
        reputation=agent.reputation,
        tier=agent.tier,
        currency=agent.currency,
        status=agent.status,
        created_at=agent.created_at,
    )


@router.post("/auth/validate", response_model=ValidateResponse)
def validate(x_api_key: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.api_key == x_api_key).first()
    if not agent:
        return ValidateResponse(valid=False)
    return ValidateResponse(valid=True, agent_id=agent.agent_id)
