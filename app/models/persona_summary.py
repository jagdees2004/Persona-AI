"""
SQLAlchemy model: PersonaSummary (per-persona conversation summaries).
"""

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from core.database import Base


class PersonaSummary(Base):
    __tablename__ = "persona_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    persona = Column(String(64), nullable=False, index=True)
    summary = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
