from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base


class UserFile(Base):
    __tablename__ = "user_files"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename    = Column(String, nullable=False)
    file_type   = Column(String, default="pdf")
    size_bytes  = Column(Integer, nullable=False)
    pages       = Column(Integer, default=0)
    chunks      = Column(Integer, default=0)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="files")
