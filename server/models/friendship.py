from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from server.db.database import Base


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("agent_id", "friend_id", name="uq_friendship_pair"),
        Index("idx_friendship_agent", "agent_id"),
    )
