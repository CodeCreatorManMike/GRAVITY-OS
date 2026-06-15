from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    title         = Column(String, default="")
    start_at      = Column(DateTime(timezone=True), nullable=False)
    end_at        = Column(DateTime(timezone=True), nullable=False)
    all_day       = Column(Boolean, default=False)
    calendar_name = Column(String, default="")
    source        = Column(String, default="caldav")   # caldav | google | manual
    uid           = Column(String, default="")         # original calendar UID for dedup
    synced_at     = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="calendar_events")

    __table_args__ = (
        UniqueConstraint("user_id", "uid", "source", name="uq_calendar_event_user_uid_source"),
    )
