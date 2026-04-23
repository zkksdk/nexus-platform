import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.db.redis import get_redis
from server.db.database import get_db
from server.models import Agent
from server.schemas.agent import AgentRegister, AgentRegisterWithKey, AgentResponse, ValidateResponse
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


@router.post("/auth/register-with-key", response_model=AgentResponse)
async def register_with_key(payload: AgentRegisterWithKey, db: Session = Depends(get_db)):
    existing = db.query(Agent).filter(Agent.agent_id == payload.agent_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Agent ID already registered")

    redis = await get_redis()
    bootstrap_key = f"nexus:human:bootstrap-key:{payload.bootstrap_api_key}"
    key_data = await redis.hgetall(bootstrap_key)
    if not key_data:
        raise HTTPException(status_code=400, detail="Invalid bootstrap_api_key")
    if key_data.get("used") == "1":
        raise HTTPException(status_code=400, detail="bootstrap_api_key has already been used")

    if db.query(Agent).filter(Agent.api_key == payload.bootstrap_api_key).first():
        raise HTTPException(status_code=400, detail="bootstrap_api_key already bound")

    agent = Agent(
        agent_id=payload.agent_id,
        api_key=payload.bootstrap_api_key,
        name=payload.name,
        avatar_url=payload.avatar_url,
        personality=payload.personality,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

    await redis.hset(bootstrap_key, mapping={"used": "1", "agent_id": payload.agent_id})
    get_api_key_cache()[agent.api_key] = agent.id

    return AgentResponse(
        agent_id=agent.agent_id,
        api_key=agent.api_key,
        name=agent.name,
        avatar_url=agent.avatar_url,
        personality=agent.personality,
        reputation=agent.reputation,
        tier=agent.tier,
        currency=agent.currency,
        status=agent.status,
        created_at=agent.created_at,
    )
