"""
SQLAlchemy model: UserProfile (global user data).
"""

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(32), nullable=True)
    location = Column(String(128), nullable=True)
    interests = Column(Text, nullable=True)  # JSON string
    communication_style = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
