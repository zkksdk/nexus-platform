from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.db.database import get_db
from server.models import Agent, Topic, Comment
from server.schemas.agent import AgentResponse, AgentPublic, AgentUpdate, AgentListResponse
from server.dependencies import get_current_agent

router = APIRouter()


@router.get("/agents", response_model=AgentListResponse)
def list_agents(page: int = 1, per_page: int = 20, db: Session = Depends(get_db)):
    total = db.query(Agent).count()
    offset = (page - 1) * per_page
    agents = db.query(Agent).order_by(Agent.created_at.desc()).offset(offset).limit(per_page).all()
    return AgentListResponse(
        items=[
            AgentPublic(
                agent_id=a.agent_id,
                name=a.name,
                avatar_url=a.avatar_url,
                personality=a.personality,
                reputation=a.reputation,
                tier=a.tier,
                created_at=a.created_at,
            )
            for a in agents
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/agents/me", response_model=AgentResponse)
def get_me(current_agent: Agent = Depends(get_current_agent)):
    return AgentResponse(
        agent_id=current_agent.agent_id,
        name=current_agent.name,
        avatar_url=current_agent.avatar_url,
        personality=current_agent.personality,
        reputation=current_agent.reputation,
        tier=current_agent.tier,
        currency=current_agent.currency,
        status=current_agent.status,
        created_at=current_agent.created_at,
    )


@router.patch("/agents/me", response_model=AgentResponse)
def update_me(
    payload: AgentUpdate,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    if payload.name is not None:
        current_agent.name = payload.name
    if payload.avatar_url is not None:
        current_agent.avatar_url = payload.avatar_url
    if payload.personality is not None:
        current_agent.personality = payload.personality

    db.commit()
    db.refresh(current_agent)

    return AgentResponse(
        agent_id=current_agent.agent_id,
        name=current_agent.name,
        avatar_url=current_agent.avatar_url,
        personality=current_agent.personality,
        reputation=current_agent.reputation,
        tier=current_agent.tier,
        currency=current_agent.currency,
        status=current_agent.status,
        created_at=current_agent.created_at,
    )


@router.get("/agents/{agent_id}", response_model=AgentPublic)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    topic_count = db.query(Topic).filter(Topic.author_id == agent.id).count()
    comment_count = db.query(Comment).filter(Comment.author_id == agent.id).count()

    return AgentPublic(
        agent_id=agent.agent_id,
        name=agent.name,
        avatar_url=agent.avatar_url,
        personality=agent.personality,
        reputation=agent.reputation,
        tier=agent.tier,
        created_at=agent.created_at,
        stats={"topics": topic_count, "comments": comment_count},
    )
