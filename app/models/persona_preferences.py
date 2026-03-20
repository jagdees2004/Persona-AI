"""
SQLAlchemy model: PersonaPreferences (per-persona user settings).
"""

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from core.database import Base


class PersonaPreferences(Base):
    __tablename__ = "persona_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    persona = Column(String(64), nullable=False, index=True)
    preferences = Column(Text, nullable=False)  # JSON string
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
