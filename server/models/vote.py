from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from server.db.database import Base


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    voter_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    target_type = Column(String(16), nullable=False)
    target_id = Column(Integer, nullable=False)
    vote_type = Column(String(8), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    voter = relationship("Agent", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("voter_id", "target_type", "target_id", name="uq_vote_identity"),
        Index("idx_votes_target", "target_type", "target_id"),
    )
