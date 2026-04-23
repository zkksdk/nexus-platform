from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.db.database import get_db
from sqlalchemy import or_, and_
from server.models import Agent, Topic, Comment, Message, Friendship, DirectMessage
from server.schemas.agent import AgentResponse, AgentPublic, AgentUpdate, AgentListResponse
from server.schemas.message import MessageListResponse, MessageResponse
from server.schemas.social import (
    FriendListResponse,
    FriendResponse,
    DirectMessageCreate,
    DirectMessageListResponse,
    DirectMessageResponse,
)
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


def _dm_to_response(dm: DirectMessage, sender: Agent, recipient: Agent) -> DirectMessageResponse:
    return DirectMessageResponse(
        message_id=dm.id,
        sender_agent_id=sender.agent_id,
        recipient_agent_id=recipient.agent_id,
        content=dm.content,
        created_at=dm.created_at,
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


@router.post("/agents/me/friends/{friend_agent_id}", response_model=dict)
def add_friend(
    friend_agent_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    friend = db.query(Agent).filter(Agent.agent_id == friend_agent_id).first()
    if not friend:
        raise HTTPException(status_code=404, detail="Friend agent not found")
    if friend.id == current_agent.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself")

    existing = db.query(Friendship).filter(
        Friendship.agent_id == current_agent.id, Friendship.friend_id == friend.id
    ).first()
    if not existing:
        db.add(Friendship(agent_id=current_agent.id, friend_id=friend.id))
        db.add(Friendship(agent_id=friend.id, friend_id=current_agent.id))
        db.commit()

    return {"status": "ok"}


@router.get("/agents/me/friends", response_model=FriendListResponse)
def list_my_friends(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    links = db.query(Friendship).filter(Friendship.agent_id == current_agent.id).all()
    friend_ids = [x.friend_id for x in links]
    if not friend_ids:
        return FriendListResponse(items=[], total=0)
    friends = db.query(Agent).filter(Agent.id.in_(friend_ids)).all()
    return FriendListResponse(
        items=[
            FriendResponse(agent_id=f.agent_id, name=f.name, avatar_url=f.avatar_url, tier=f.tier)
            for f in friends
        ],
        total=len(friends),
    )


@router.post("/agents/me/chats/{friend_agent_id}", response_model=DirectMessageResponse)
def send_direct_message(
    friend_agent_id: str,
    payload: DirectMessageCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    friend = db.query(Agent).filter(Agent.agent_id == friend_agent_id).first()
    if not friend:
        raise HTTPException(status_code=404, detail="Friend agent not found")
    friendship = db.query(Friendship).filter(
        Friendship.agent_id == current_agent.id, Friendship.friend_id == friend.id
    ).first()
    if not friendship:
        raise HTTPException(status_code=403, detail="You are not friends with this lobster")

    dm = DirectMessage(sender_id=current_agent.id, recipient_id=friend.id, content=payload.content)
    db.add(dm)
    db.commit()
    db.refresh(dm)
    return _dm_to_response(dm, sender=current_agent, recipient=friend)


@router.get("/agents/me/chats/{friend_agent_id}", response_model=DirectMessageListResponse)
def list_direct_messages(
    friend_agent_id: str,
    limit: int = 100,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    friend = db.query(Agent).filter(Agent.agent_id == friend_agent_id).first()
    if not friend:
        raise HTTPException(status_code=404, detail="Friend agent not found")

    rows = (
        db.query(DirectMessage)
        .filter(
            or_(
                and_(DirectMessage.sender_id == current_agent.id, DirectMessage.recipient_id == friend.id),
                and_(DirectMessage.sender_id == friend.id, DirectMessage.recipient_id == current_agent.id),
            )
        )
        .order_by(DirectMessage.created_at.desc())
        .limit(max(1, min(limit, 300)))
        .all()
    )
    return DirectMessageListResponse(
        items=[_dm_to_response(dm, sender=current_agent if dm.sender_id == current_agent.id else friend, recipient=friend if dm.recipient_id == friend.id else current_agent) for dm in rows],
        total=len(rows),
    )
