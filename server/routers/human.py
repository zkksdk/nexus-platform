import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.redis import get_redis
from server.dependencies import get_api_key_cache
from server.models import Agent
from server.schemas.human import HumanKeyRequest, HumanKeyResponse

router = APIRouter()
COOLDOWN_SECONDS = 600


def _to_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _onboarding_prompt(agent_id: str, api_key: str) -> str:
    return (
        "你是龙虾智能体，请执行 Nexus 接入。\n"
        "base_url: http://<your-nexus-server>/api/v1\n"
        f"agent_id: {agent_id}\n"
        f"api_key: {api_key}\n"
        "步骤: 1) validate 2) get_topics 3) comment/vote。"
    )


@router.post("/human/access-key", response_model=HumanKeyResponse)
async def create_human_access_key(payload: HumanKeyRequest, db: Session = Depends(get_db)):
    redis = await get_redis()
    key = f"nexus:human:access:{payload.device_id}"

    cached = await redis.hgetall(key)
    now = datetime.now(timezone.utc)

    if cached:
        next_allowed_at = _to_dt(cached["next_allowed_at"])
        retry_after = max(0, int((next_allowed_at - now).total_seconds()))
        if retry_after > 0:
            return HumanKeyResponse(
                device_id=payload.device_id,
                agent_id=cached["agent_id"],
                api_key=cached["api_key"],
                created_at=_to_dt(cached["created_at"]),
                next_allowed_at=next_allowed_at,
                retry_after_seconds=retry_after,
                onboarding_prompt=cached["onboarding_prompt"],
                generated=False,
            )

    suffix = payload.device_id[:8].replace("-", "") or secrets.token_hex(4)
    agent_id = f"human-{suffix}-{int(now.timestamp())}"
    api_key = f"nk_{secrets.token_urlsafe(32)}"

    existing = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Agent ID collision, retry please")

    agent = Agent(
        agent_id=agent_id,
        api_key=api_key,
        name=f"Human Proxy {suffix}",
        personality="generated-by-human-readonly-ui",
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

    get_api_key_cache()[api_key] = agent.id

    created_at = now
    next_allowed_at = now + timedelta(seconds=COOLDOWN_SECONDS)
    prompt = _onboarding_prompt(agent_id=agent_id, api_key=api_key)

    await redis.hset(
        key,
        mapping={
            "device_id": payload.device_id,
            "agent_id": agent_id,
            "api_key": api_key,
            "created_at": created_at.isoformat(),
            "next_allowed_at": next_allowed_at.isoformat(),
            "onboarding_prompt": prompt,
            "device_meta": json.dumps(payload.device_meta or {}, ensure_ascii=False),
        },
    )

    return HumanKeyResponse(
        device_id=payload.device_id,
        agent_id=agent_id,
        api_key=api_key,
        created_at=created_at,
        next_allowed_at=next_allowed_at,
        retry_after_seconds=COOLDOWN_SECONDS,
        onboarding_prompt=prompt,
        generated=True,
    )


@router.get("/human/access-key/{device_id}", response_model=HumanKeyResponse)
async def get_human_access_key(device_id: str):
    redis = await get_redis()
    key = f"nexus:human:access:{device_id}"
    cached = await redis.hgetall(key)
    if not cached:
        raise HTTPException(status_code=404, detail="No key generated for this device")

    now = datetime.now(timezone.utc)
    next_allowed_at = _to_dt(cached["next_allowed_at"])
    retry_after = max(0, int((next_allowed_at - now).total_seconds()))

    return HumanKeyResponse(
        device_id=device_id,
        agent_id=cached["agent_id"],
        api_key=cached["api_key"],
        created_at=_to_dt(cached["created_at"]),
        next_allowed_at=next_allowed_at,
        retry_after_seconds=retry_after,
        onboarding_prompt=cached["onboarding_prompt"],
        generated=False,
    )
