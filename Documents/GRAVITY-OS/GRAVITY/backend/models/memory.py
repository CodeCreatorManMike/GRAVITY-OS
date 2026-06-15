from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from backend.database import Base


class Memory(Base):
    __tablename__ = "memories"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content         = Column(Text, nullable=False)
    embedding       = Column(Vector(384), nullable=False)
    memory_type     = Column(String, default="conversation")  # conversation|goal|document|pattern|insight
    source          = Column(String, default="")
    relevance_score = Column(Float, default=1.0)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="memories")
