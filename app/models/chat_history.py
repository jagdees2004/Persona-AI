"""
SQLAlchemy model: ChatHistory (persona-based conversation logs).
"""

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from core.database import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    persona = Column(String(64), nullable=False, index=True)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
