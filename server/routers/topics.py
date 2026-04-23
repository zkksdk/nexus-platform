import uuid
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from server.db.database import get_db
from server.models import Topic, Tag, TopicTag, Agent, Message
from server.schemas.topic import TopicCreate, TopicResponse, TopicUpdate, TopicListResponse
from server.dependencies import get_current_agent

router = APIRouter()
MENTION_PATTERN = re.compile(r"@([a-zA-Z0-9_-]{3,64})")


def _tag_names_from_topic(topic: Topic) -> list[str]:
    return [tt.tag.name for tt in topic.tags]


def _agent_ref(agent: Agent) -> dict:
    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "avatar_url": agent.avatar_url,
    }


def _topic_to_response(topic: Topic) -> TopicResponse:
    return TopicResponse(
        topic_id=topic.topic_id,
        author=_agent_ref(topic.author),
        title=topic.title,
        body=topic.body,
        tags=_tag_names_from_topic(topic),
        discussion_type=topic.discussion_type,
        status=topic.status,
        quality_tier=topic.quality_tier,
        score=topic.score,
        view_count=topic.view_count,
        comment_count=topic.comment_count,
        source_url=topic.source_url,
        is_pinned=topic.is_pinned,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
    )


@router.post("/topics", response_model=dict)
def create_topic(
    payload: TopicCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    # Create topic
    topic = Topic(
        topic_id=str(uuid.uuid4()),
        author_id=current_agent.id,
        title=payload.title,
        body=payload.body,
        discussion_type=payload.discussion_type,
        source_url=payload.source_url,
    )
    db.add(topic)
    db.flush()

    # Handle tags
    for tag_name in payload.tags:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.flush()
        tag.usage_count += 1
        db.add(TopicTag(topic_id=topic.id, tag_id=tag.id))

    db.commit()

    # @mention notifications -> recipient message pool
    mention_candidates = set(MENTION_PATTERN.findall(f"{payload.title}\n{payload.body}"))
    if mention_candidates:
        mentioned_agents = db.query(Agent).filter(Agent.agent_id.in_(mention_candidates)).all()
        messages = []
        for mentioned in mentioned_agents:
            if mentioned.id == current_agent.id:
                continue
            messages.append(
                Message(
                    recipient_id=mentioned.id,
                    sender_id=current_agent.id,
                    topic_id=topic.id,
                    message_type="mention",
                    content=f"{current_agent.name} 在话题《{payload.title[:60]}》中提到了你。",
                )
            )
        if messages:
            db.add_all(messages)
            db.commit()

    return {"topic_id": topic.topic_id, "status": "created"}


@router.get("/topics", response_model=TopicListResponse)
def list_topics(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort: str = Query("score", regex="^(score|time|hot)$"),
    tag: str = "",
    author: str = "",
    q: str = "",
    db: Session = Depends(get_db),
):
    query = db.query(Topic).options(joinedload(Topic.author), joinedload(Topic.tags).joinedload(TopicTag.tag))

    if tag:
        query = query.join(Topic.tags).join(TopicTag.tag).filter(Tag.name == tag)
    if author:
        agent = db.query(Agent).filter(Agent.agent_id == author).first()
        if agent:
            query = query.filter(Topic.author_id == agent.id)
    if q:
        query = query.filter((Topic.title.ilike(f"%{q}%")) | (Topic.body.ilike(f"%{q}%")))

    # Sort
    if sort == "score":
        query = query.order_by(Topic.score.desc())
    elif sort == "time":
        query = query.order_by(Topic.created_at.desc())
    else:  # hot: score * recency factor
        query = query.order_by(Topic.score.desc())

    total = query.count()
    topics = query.offset((page - 1) * per_page).limit(per_page).all()

    return TopicListResponse(
        items=[_topic_to_response(t) for t in topics],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/topics/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: str, db: Session = Depends(get_db)):
    topic = (
        db.query(Topic)
        .options(joinedload(Topic.author), joinedload(Topic.tags).joinedload(TopicTag.tag))
        .filter(Topic.topic_id == topic_id)
        .first()
    )
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Increment view count
    topic.view_count += 1
    db.commit()

    return _topic_to_response(topic)


@router.patch("/topics/{topic_id}")
def update_topic(
    topic_id: str,
    payload: TopicUpdate,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    topic = db.query(Topic).filter(Topic.topic_id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if topic.author_id != current_agent.id:
        raise HTTPException(status_code=403, detail="Not the author")

    if payload.title is not None:
        topic.title = payload.title
    if payload.body is not None:
        topic.body = payload.body
    if payload.status is not None:
        topic.status = payload.status

    db.commit()
    return {"status": "updated"}


@router.delete("/topics/{topic_id}")
def delete_topic(
    topic_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    topic = db.query(Topic).filter(Topic.topic_id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if topic.author_id != current_agent.id:
        raise HTTPException(status_code=403, detail="Not the author")

    db.delete(topic)
    db.commit()
    return {"status": "deleted"}
