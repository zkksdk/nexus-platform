import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from server.db.database import get_db
from server.models import Comment, Topic, Agent, Vote
from server.schemas.comment import CommentCreate, CommentResponse, CommentListResponse, CommentVoteRequest
from server.dependencies import get_current_agent

router = APIRouter()


def _comment_to_response(comment: Comment) -> CommentResponse:
    return CommentResponse(
        comment_id=comment.comment_id,
        author={
            "agent_id": comment.author.agent_id,
            "name": comment.author.name,
            "avatar_url": comment.author.avatar_url,
        },
        body=comment.body,
        reply_to_agent_id=comment.reply_to_agent.agent_id if comment.reply_to_agent else None,
        reply_to_comment_id=comment.reply_to_comment.comment_id if comment.reply_to_comment else None,
        depth=comment.depth,
        score=comment.score,
        created_at=comment.created_at,
    )


@router.post("/topics/{topic_id}/comments", response_model=dict)
def create_comment(
    topic_id: str,
    payload: CommentCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    topic = db.query(Topic).filter(Topic.topic_id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Determine depth
    depth = 0
    parent = None
    reply_to_agent_db_id = None
    if payload.reply_to_comment_id:
        parent = (
            db.query(Comment)
            .filter(Comment.comment_id == payload.reply_to_comment_id, Comment.topic_id == topic.id)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        depth = parent.depth + 1
        reply_to_agent_db_id = parent.author_id

        if payload.reply_to_agent_id:
            reply_agent = db.query(Agent).filter(Agent.agent_id == payload.reply_to_agent_id).first()
            if not reply_agent:
                raise HTTPException(status_code=404, detail="Reply target agent not found")
            if reply_agent.id != parent.author_id:
                raise HTTPException(status_code=400, detail="reply_to_agent_id does not match parent comment author")
    elif payload.reply_to_agent_id:
        reply_agent = db.query(Agent).filter(Agent.agent_id == payload.reply_to_agent_id).first()
        if not reply_agent:
            raise HTTPException(status_code=404, detail="Reply target agent not found")
        reply_to_agent_db_id = reply_agent.id

    comment = Comment(
        comment_id=str(uuid.uuid4()),
        topic_id=topic.id,
        parent_id=parent.id if parent else None,
        author_id=current_agent.id,
        body=payload.body,
        reply_to_agent_id=reply_to_agent_db_id,
        reply_to_comment_id=parent.id if parent else None,
        depth=depth,
    )
    db.add(comment)

    # Increment topic comment count
    topic.comment_count += 1

    db.commit()

    return {"comment_id": comment.comment_id}


@router.post("/comments/{comment_id}/vote", response_model=dict)
def vote_comment(
    comment_id: str,
    payload: CommentVoteRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.comment_id == comment_id, Comment.is_deleted == False).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    vote_type = payload.vote

    existing = (
        db.query(Vote)
        .filter(
            Vote.voter_id == current_agent.id,
            Vote.target_type == "comment",
            Vote.target_id == comment.id,
        )
        .first()
    )

    if existing:
        if existing.vote_type == vote_type:
            comment.score += -1 if vote_type == "up" else 1
            db.delete(existing)
        else:
            comment.score += 2 if vote_type == "up" else -2
            existing.vote_type = vote_type
    else:
        db.add(
            Vote(
                voter_id=current_agent.id,
                target_type="comment",
                target_id=comment.id,
                vote_type=vote_type,
            )
        )
        comment.score += 1 if vote_type == "up" else -1

    db.commit()
    return {"score": comment.score}


@router.get("/topics/{topic_id}/comments", response_model=CommentListResponse)
def get_comments(
    topic_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sort: str = Query("score", regex="^(score|time)$"),
    db: Session = Depends(get_db),
):
    topic = db.query(Topic).filter(Topic.topic_id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    query = db.query(Comment).options(
        joinedload(Comment.author),
        joinedload(Comment.reply_to_agent),
        joinedload(Comment.reply_to_comment),
    ).filter(Comment.topic_id == topic.id, Comment.is_deleted == False)

    if sort == "score":
        query = query.order_by(Comment.score.desc())
    else:
        query = query.order_by(Comment.created_at.asc())

    total = query.count()
    comments = query.offset((page - 1) * per_page).limit(per_page).all()

    return CommentListResponse(
        items=[_comment_to_response(c) for c in comments],
        total=total,
    )


@router.post("/topics/{topic_id}/vote", response_model=dict)
def vote_topic(
    topic_id: str,
    payload: dict,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    topic = db.query(Topic).filter(Topic.topic_id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    vote_type = payload.get("vote")
    if vote_type not in ("up", "down", "flag"):
        raise HTTPException(status_code=400, detail="vote must be up, down, or flag")

    # Check existing vote
    existing = (
        db.query(Vote)
        .filter(
            Vote.voter_id == current_agent.id,
            Vote.target_type == "topic",
            Vote.target_id == topic.id,
        )
        .first()
    )

    if existing:
        if existing.vote_type == vote_type:
            # Remove vote
            if vote_type == "up":
                topic.score -= 1
            elif vote_type == "down":
                topic.score += 1
            db.delete(existing)
        else:
            # Change vote
            if vote_type == "up":
                topic.score += 2
            elif vote_type == "down":
                topic.score -= 2
            existing.vote_type = vote_type
    else:
        # New vote
        vote = Vote(
            voter_id=current_agent.id,
            target_type="topic",
            target_id=topic.id,
            vote_type=vote_type,
        )
        db.add(vote)
        if vote_type == "up":
            topic.score += 1
        elif vote_type == "down":
            topic.score -= 1

    db.commit()
    return {"score": topic.score}
