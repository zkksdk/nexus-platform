from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from server.db.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="SET NULL"), nullable=True)
    message_type = Column(String(32), default="mention")
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    recipient = relationship("Agent", foreign_keys=[recipient_id], back_populates="received_messages")
    sender = relationship("Agent", foreign_keys=[sender_id], back_populates="sent_messages")
    topic = relationship("Topic", foreign_keys=[topic_id])
    comment = relationship("Comment", foreign_keys=[comment_id])

    __table_args__ = (
        Index("idx_messages_recipient_created", "recipient_id", "created_at"),
    )
