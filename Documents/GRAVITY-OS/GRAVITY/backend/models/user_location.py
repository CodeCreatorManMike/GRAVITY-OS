from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class UserLocation(Base):
    __tablename__ = "user_locations"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    latitude   = Column(Float, nullable=False)
    longitude  = Column(Float, nullable=False)
    city       = Column(String, default="")
    timezone   = Column(String, default="Europe/London")
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="location")
