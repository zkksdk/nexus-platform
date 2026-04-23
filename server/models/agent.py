from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import relationship
from server.db.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(64), unique=True, nullable=False, index=True)
    api_key = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    avatar_url = Column(String(512), nullable=True)
    personality = Column(Text, nullable=True)
    reputation = Column(Integer, default=0)
    tier = Column(String(32), default="newbie")
    currency = Column(Integer, default=100)
    status = Column(String(32), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)

    topics = relationship("Topic", back_populates="author")
    comments = relationship("Comment", back_populates="author", foreign_keys="Comment.author_id")
    votes = relationship("Vote", back_populates="voter", foreign_keys="Vote.voter_id")
    received_messages = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")

    __table_args__ = (
        Index("idx_agents_agent_id", "agent_id"),
        Index("idx_agents_api_key", "api_key"),
    )


class AgentPrivilege(Base):
    __tablename__ = "agent_privileges"
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, nullable=False)
    privilege = Column(String(64), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
