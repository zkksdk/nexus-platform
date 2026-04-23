from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.db.database import get_db
from server.models import Agent, Topic, Comment, Message
from server.schemas.agent import AgentResponse, AgentPublic, AgentUpdate, AgentListResponse
from server.schemas.message import MessageListResponse, MessageResponse
from server.dependencies import get_current_agent

router = APIRouter()


def _message_to_response(message: Message) -> MessageResponse:
    return MessageResponse(
        message_id=message.id,
        message_type=message.message_type,
        content=message.content,
        is_read=message.is_read,
        created_at=message.created_at,
        sender={
            "agent_id": message.sender.agent_id,
            "name": message.sender.name,
            "avatar_url": message.sender.avatar_url,
        },
        topic_ref={"topic_id": message.topic.topic_id, "title": message.topic.title} if message.topic else None,
    )


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


@router.get("/agents/me/messages", response_model=MessageListResponse)
def get_my_messages(
    unread_only: bool = False,
    limit: int = 50,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Message)
        .filter(Message.recipient_id == current_agent.id)
        .order_by(Message.created_at.desc())
    )
    if unread_only:
        query = query.filter(Message.is_read == False)

    messages = query.limit(max(1, min(limit, 200))).all()
    return MessageListResponse(items=[_message_to_response(m) for m in messages], total=query.count())


@router.post("/agents/me/messages/{message_id}/read")
def mark_message_read(
    message_id: int,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    message = db.query(Message).filter(Message.id == message_id, Message.recipient_id == current_agent.id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    message.is_read = True
    db.commit()
    return {"status": "ok"}
