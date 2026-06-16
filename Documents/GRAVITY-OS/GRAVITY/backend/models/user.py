from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    id                     = Column(Integer, primary_key=True, index=True)
    email                  = Column(String, unique=True, index=True, nullable=False)
    name                   = Column(String, nullable=False)
    hashed_password        = Column(String, nullable=False)
    is_active              = Column(Boolean, default=True)
    created_at             = Column(DateTime(timezone=True), server_default=func.now())
    personality_summary    = Column(Text, default="")
    motivation_style       = Column(String, default="")
    energy_pattern         = Column(String, default="")
    self_awareness_level   = Column(String, default="")
    failure_response       = Column(String, default="")
    feedback_preference    = Column(String, default="direct")
    onboarding_complete    = Column(Boolean, default=False)
    onboarding_phase       = Column(Integer, default=0)
    wake_time              = Column(String, default="07:00")
    sleep_time             = Column(String, default="23:00")
    peak_focus_windows     = Column(JSON, default=list)
    known_dead_zones       = Column(JSON, default=list)
    realistic_daily_hours  = Column(Float, default=1.0)
    avoidance_behaviours   = Column(JSON, default=list)
    goals             = relationship("Goal",            back_populates="user", cascade="all, delete-orphan")
    habits            = relationship("Habit",           back_populates="user", cascade="all, delete-orphan")
    nudges            = relationship("Nudge",           back_populates="user", cascade="all, delete-orphan")
    nudge_settings    = relationship("NudgeSettings",   back_populates="user", uselist=False, cascade="all, delete-orphan")
    health_data        = relationship("HealthData",       back_populates="user", cascade="all, delete-orphan")
    cycle_reviews      = relationship("CycleReview",      back_populates="user", cascade="all, delete-orphan")
    behaviour_patterns = relationship("BehaviourPattern", back_populates="user", cascade="all, delete-orphan")
    push_tokens        = relationship("PushToken",        back_populates="user", cascade="all, delete-orphan")
    memories           = relationship("Memory",           back_populates="user", cascade="all, delete-orphan")
    calendar_events    = relationship("CalendarEvent",    back_populates="user", cascade="all, delete-orphan")
    location           = relationship("UserLocation",     back_populates="user", uselist=False, cascade="all, delete-orphan")
    files              = relationship("UserFile",          back_populates="user", cascade="all, delete-orphan")
    ai_interactions    = relationship("AIInteraction",     back_populates="user", cascade="all, delete-orphan")

class Goal(Base):
    __tablename__ = "goals"
    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False)
    statement           = Column(Text, default="")
    real_why            = Column(Text, default="")
    likelihood_score    = Column(Float, default=0.0)
    milestone_structure = Column(JSON, default=list)
    risk_factors        = Column(JSON, default=list)
    cycle_start         = Column(String, default="")
    cycle_end           = Column(String, default="")
    is_active           = Column(Boolean, default=True)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="goals")

class Habit(Base):
    __tablename__ = "habits"
    id                = Column(Integer, primary_key=True, index=True)
    user_id           = Column(Integer, ForeignKey("users.id"), nullable=False)
    name              = Column(String, nullable=False)
    is_non_negotiable = Column(Boolean, default=False)
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="habits")
    logs = relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")

class HabitLog(Base):
    __tablename__ = "habit_logs"
    id         = Column(Integer, primary_key=True, index=True)
    habit_id   = Column(Integer, ForeignKey("habits.id"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    completed  = Column(Boolean, default=True)
    logged_at  = Column(DateTime(timezone=True), server_default=func.now())
    date       = Column(String, nullable=False)
    habit = relationship("Habit", back_populates="logs")

class Nudge(Base):
    __tablename__ = "nudges"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    category     = Column(String, default="")
    intensity    = Column(String, default="ambient")
    tone         = Column(String, default="direct")   # mirrors user.feedback_preference at send time
    message      = Column(Text, default="")
    sub_message  = Column(Text, default="")
    action_label = Column(String, default="Dismiss")
    reason       = Column(Text, default="")
    acknowledged = Column(Boolean, default=False)
    sent_at      = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="nudges")


class NudgeSettings(Base):
    """Per-user nudge preferences — one row per user, created on first access."""
    __tablename__ = "nudge_settings"
    id                   = Column(Integer, primary_key=True, index=True)
    user_id              = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    quiet_hours_start    = Column(String, default="22:00")
    quiet_hours_end      = Column(String, default="08:00")
    rest_days            = Column(JSON, default=list)       # e.g. ["Sunday"]
    sensitivity_habit    = Column(Float, default=1.0)
    sensitivity_focus    = Column(Float, default=1.0)
    sensitivity_fitness  = Column(Float, default=1.0)
    sensitivity_sleep    = Column(Float, default=1.0)
    sensitivity_spending = Column(Float, default=1.0)
    user = relationship("User", back_populates="nudge_settings")
