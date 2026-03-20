"""
Database setup with MongoDB (motor async driver).
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# MongoDB client (lazy-initialized on startup)
_client: AsyncIOMotorClient = None
_db = None


def get_client() -> AsyncIOMotorClient:
    """Get the MongoDB client instance."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
    return _client


def get_db():
    """Get the MongoDB database instance."""
    global _db
    if _db is None:
        client = get_client()
        _db = client[settings.MONGODB_DB_NAME]
    return _db


async def init_db():
    """
    Initialize MongoDB: create indexes for efficient queries.
    Called on application startup.
    """
    db = get_db()

    # user_profiles: unique index on user_id (acts as primary key)
    await db.user_profiles.create_index("user_id", unique=True)

    # chat_history: compound index for fast lookups
    await db.chat_history.create_index([("user_id", 1), ("persona", 1)])
    await db.chat_history.create_index("timestamp")

    # persona_summaries: unique compound index (one summary per user+persona)
    await db.persona_summaries.create_index(
        [("user_id", 1), ("persona", 1)], unique=True
    )

    # persona_preferences: unique compound index
    await db.persona_preferences.create_index(
        [("user_id", 1), ("persona", 1)], unique=True
    )

    # short_term_memory: compound index + TTL (optional)
    await db.short_term_memory.create_index(
        [("user_id", 1), ("persona", 1)]
    )

    logger.info("✅ MongoDB indexes created successfully")


async def close_db():
    """Close the MongoDB connection. Called on application shutdown."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")
