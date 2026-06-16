from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base


class AIInteraction(Base):
    """Every AI-generated message/action. UUID ties back to outcome."""
    __tablename__ = "ai_interactions"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # mode: nudge | challenger | onboarding | voice | document | review | layout
    mode        = Column(String, nullable=False)
    provider    = Column(String, nullable=False)   # groq | anthropic | ollama
    model       = Column(String, nullable=False)
    message     = Column(Text, nullable=False)     # the AI output shown to user
    tool_used   = Column(String, nullable=True)    # voice tool name if applicable
    prompt_tokens  = Column(Integer, default=0)
    output_tokens  = Column(Integer, default=0)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    outcomes = relationship("AIOutcome", back_populates="interaction", cascade="all, delete-orphan")
    user     = relationship("User", back_populates="ai_interactions")


class AIOutcome(Base):
    """Did the user act on the AI's output? Core training signal."""
    __tablename__ = "ai_outcomes"

    id               = Column(Integer, primary_key=True, index=True)
    interaction_id   = Column(Integer, ForeignKey("ai_interactions.id"), nullable=False, index=True)
    acted            = Column(Boolean, nullable=True)   # None = not yet reported
    acted_within_hours = Column(Float, nullable=True)
    user_rating      = Column(Integer, nullable=True)   # 1-5, optional thumbs
    recorded_at      = Column(DateTime(timezone=True), server_default=func.now())

    interaction = relationship("AIInteraction", back_populates="outcomes")
