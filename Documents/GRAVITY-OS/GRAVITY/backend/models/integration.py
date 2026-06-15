from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class HealthData(Base):
    """Daily health snapshot pushed from Apple Health via the app."""
    __tablename__ = "health_data"
    id                = Column(Integer, primary_key=True, index=True)
    user_id           = Column(Integer, ForeignKey("users.id"), nullable=False)
    date              = Column(String, nullable=False)          # YYYY-MM-DD
    steps             = Column(Integer, default=0)
    sleep_hours       = Column(Float, default=0.0)             # total hours in bed
    sleep_quality     = Column(String, default="unknown")      # poor / fair / good / unknown
    workout_minutes   = Column(Integer, default=0)
    workout_type      = Column(String, default="")             # walk / run / gym / etc.
    heart_rate_avg    = Column(Integer, default=0)
    calories_active   = Column(Integer, default=0)
    synced_at         = Column(DateTime(timezone=True), server_default=func.now())
    user              = relationship("User", back_populates="health_data")


class CycleReview(Base):
    """Snapshot of a completed 6-month cycle with AI-generated analysis."""
    __tablename__ = "cycle_reviews"
    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_id         = Column(Integer, ForeignKey("goals.id"), nullable=True)
    cycle_start     = Column(String, default="")
    cycle_end       = Column(String, default="")
    final_likelihood= Column(Float, default=0.0)
    habits_avg_completion = Column(Float, default=0.0)   # 0.0–1.0
    nudge_response_rate   = Column(Float, default=0.0)
    ai_summary      = Column(Text, default="")           # AI-generated cycle summary
    patterns_log    = Column(JSON, default=list)         # patterns identified during cycle
    status          = Column(String, default="pending")  # pending / in_progress / complete
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    user            = relationship("User", back_populates="cycle_reviews")


class BehaviourPattern(Base):
    """AI-identified behavioural patterns — rebuilt nightly by pattern_service."""
    __tablename__ = "behaviour_patterns"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    pattern     = Column(Text, nullable=False)    # plain English description
    category    = Column(String, default="")      # habit / focus / fitness / sleep / general
    confidence  = Column(Float, default=1.0)      # 0.0–1.0
    first_seen  = Column(String, default="")      # YYYY-MM-DD
    last_seen   = Column(String, default="")      # YYYY-MM-DD
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    user        = relationship("User", back_populates="behaviour_patterns")
