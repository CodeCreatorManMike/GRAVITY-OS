from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base


class Webhook(Base):
    """A user-configured inbound endpoint or outbound event subscription."""

    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    direction = Column(String(16), nullable=False)  # inbound / outbound
    event_type = Column(String(64), nullable=False, default="*")
    target_url = Column(Text, nullable=True)
    token = Column(String(128), nullable=True, unique=True, index=True)
    signing_secret = Column(String(256), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    last_status = Column(Integer, nullable=True)
    last_error = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="webhooks")
