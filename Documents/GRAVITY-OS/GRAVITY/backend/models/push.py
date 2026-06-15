from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class PushToken(Base):
    """Expo push notification token per user device."""
    __tablename__ = "push_tokens"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    token       = Column(String, nullable=False, unique=True)   # ExponentPushToken[...]
    platform    = Column(String, default="ios")                 # ios / android
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user        = relationship("User", back_populates="push_tokens")
