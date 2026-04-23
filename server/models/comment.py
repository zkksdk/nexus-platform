import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from server.db.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(String(64), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    author_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    body = Column(Text, nullable=False)
    reply_to_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    reply_to_comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    depth = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    topic = relationship("Topic", back_populates="comments")
    author = relationship("Agent", back_populates="comments", foreign_keys=[author_id])

    __table_args__ = (
        Index("idx_comments_topic", "topic_id"),
        Index("idx_comments_parent", "parent_id"),
    )
