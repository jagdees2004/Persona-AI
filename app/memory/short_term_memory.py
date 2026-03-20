"""
Short-term memory: in-memory cache for recent messages per user+persona.
Thread-safe in-memory store with MongoDB persistence for restart survival.
"""

import logging
from collections import defaultdict
from threading import Lock
from typing import Optional
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory store: key = "user:{user_id}:persona:{persona}:recent"
_memory_store: dict[str, list[dict]] = defaultdict(list)
_lock = Lock()

MAX_RECENT = settings.SHORT_TERM_MEMORY_LIMIT


def _key(user_id: str, persona: str) -> str:
    return f"user:{user_id}:persona:{persona}:recent"


def add_message(user_id: str, persona: str, role: str, content: str) -> None:
    """Add a message to short-term memory (in-memory)."""
    k = _key(user_id, persona)
    entry = {"role": role, "content": content}
    with _lock:
        _memory_store[k].append(entry)
        # Trim to max limit
        if len(_memory_store[k]) > MAX_RECENT:
            _memory_store[k] = _memory_store[k][-MAX_RECENT:]
    logger.debug(f"Added {role} message to short-term memory for {k}")


async def add_message_persistent(db, user_id: str, persona: str, role: str, content: str) -> None:
    """Add a message to both in-memory and MongoDB short-term memory."""
    # In-memory for fast access
    add_message(user_id, persona, role, content)

    # Persist to MongoDB for restart survival
    try:
        await db.short_term_memory.insert_one({
            "user_id": user_id,
            "persona": persona,
            "role": role,
            "content": content,
        })
    except Exception as e:
        logger.error(f"Failed to persist short-term message to MongoDB: {e}")


def get_recent(user_id: str, persona: str, limit: Optional[int] = None) -> list[dict]:
    """Get recent messages from short-term memory (in-memory)."""
    k = _key(user_id, persona)
    with _lock:
        messages = _memory_store.get(k, [])
        if limit:
            return messages[-limit:]
        return list(messages)


def clear(user_id: str, persona: str) -> None:
    """Clear short-term memory for a specific user+persona (in-memory)."""
    k = _key(user_id, persona)
    with _lock:
        _memory_store.pop(k, None)
    logger.info(f"Cleared short-term memory for {k}")


async def clear_persistent(db, user_id: str, persona: str) -> None:
    """Clear short-term memory from both in-memory and MongoDB."""
    clear(user_id, persona)
    try:
        await db.short_term_memory.delete_many({
            "user_id": user_id,
            "persona": persona,
        })
    except Exception as e:
        logger.error(f"Failed to clear MongoDB short-term memory: {e}")


async def load_from_db(db, user_id: str, persona: str) -> None:
    """Load short-term memory from MongoDB into in-memory cache (on demand)."""
    k = _key(user_id, persona)
    with _lock:
        if _memory_store.get(k):
            return  # Already loaded

    try:
        cursor = db.short_term_memory.find(
            {"user_id": user_id, "persona": persona},
            {"_id": 0, "role": 1, "content": 1},
        ).sort("_id", -1).limit(MAX_RECENT)

        messages = []
        async for doc in cursor:
            messages.append({"role": doc["role"], "content": doc["content"]})

        messages.reverse()  # Oldest first

        with _lock:
            _memory_store[k] = messages

        if messages:
            logger.debug(f"Loaded {len(messages)} messages from MongoDB for {k}")
    except Exception as e:
        logger.error(f"Failed to load short-term memory from MongoDB: {e}")


def get_all_keys() -> list[str]:
    """Return all active memory keys (for debugging)."""
    with _lock:
        return list(_memory_store.keys())
