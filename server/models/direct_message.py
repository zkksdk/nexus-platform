from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from server.db.database import Base


class DirectMessage(Base):
    __tablename__ = "direct_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_dm_pair_created", "sender_id", "recipient_id", "created_at"),
    )
