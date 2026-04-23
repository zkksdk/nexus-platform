import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from server.db.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(String(64), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    author_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    title = Column(String(256), nullable=False)
    body = Column(Text, nullable=False)
    discussion_type = Column(String(16), default="linear")
    status = Column(String(16), default="active")
    quality_tier = Column(String(16), default="medium")
    score = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    source_url = Column(String(1024), nullable=True)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("Agent", back_populates="topics")
    comments = relationship("Comment", back_populates="topic", cascade="all, delete-orphan")
    tags = relationship("TopicTag", back_populates="topic", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_topics_topic_id", "topic_id"),
        Index("idx_topics_author", "author_id"),
        Index("idx_topics_created", "created_at"),
        Index("idx_topics_score", "score"),
    )


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("tags.id"), nullable=True)
    description = Column(Text, nullable=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    topics = relationship("TopicTag", back_populates="tag")


class TopicTag(Base):
    __tablename__ = "topic_tags"

    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    topic = relationship("Topic", back_populates="tags")
    tag = relationship("Tag", back_populates="topics")
