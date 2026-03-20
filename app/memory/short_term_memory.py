"""
Short-term memory: in-memory cache for recent messages per user+persona.
Replaces Redis with a thread-safe in-memory store.
"""

import logging
import json
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
    """Add a message to short-term memory."""
    k = _key(user_id, persona)
    entry = {"role": role, "content": content}
    with _lock:
        _memory_store[k].append(entry)
        # Trim to max limit
        if len(_memory_store[k]) > MAX_RECENT:
            _memory_store[k] = _memory_store[k][-MAX_RECENT:]
    logger.debug(f"Added {role} message to short-term memory for {k}")


def get_recent(user_id: str, persona: str, limit: Optional[int] = None) -> list[dict]:
    """Get recent messages from short-term memory."""
    k = _key(user_id, persona)
    with _lock:
        messages = _memory_store.get(k, [])
        if limit:
            return messages[-limit:]
        return list(messages)


def clear(user_id: str, persona: str) -> None:
    """Clear short-term memory for a specific user+persona."""
    k = _key(user_id, persona)
    with _lock:
        _memory_store.pop(k, None)
    logger.info(f"Cleared short-term memory for {k}")


def get_all_keys() -> list[str]:
    """Return all active memory keys (for debugging)."""
    with _lock:
        return list(_memory_store.keys())
