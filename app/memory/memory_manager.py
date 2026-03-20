"""
Memory Manager: orchestrates short-term + long-term memory.
Ensures strict persona isolation — ONLY accesses the current persona's memory.
"""

import logging
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from memory.short_term_memory import (
    add_message as st_add,
    get_recent as st_get_recent,
    clear as st_clear,
)
from memory.vector_memory import (
    store_embedding,
    search as vector_search,
    delete_user_persona_memory,
    get_memory_count,
)
from models.chat_history import ChatHistory
from models.persona_summary import PersonaSummary
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def store_conversation(
    db: AsyncSession,
    user_id: str,
    persona: str,
    user_message: str,
    ai_response: str,
) -> None:
    """
    Store a conversation turn in all memory layers:
    1. Short-term (in-memory)
    2. Long-term (ChromaDB vector store)
    3. Persistent (SQLite chat_history)
    """
    # 1. Short-term memory
    st_add(user_id, persona, "user", user_message)
    st_add(user_id, persona, "assistant", ai_response)

    # 2. Long-term vector memory — store the exchange as a single document
    doc_id = f"{user_id}_{persona}_{uuid.uuid4().hex[:12]}"
    combined_text = f"User: {user_message}\nAssistant: {ai_response}"
    try:
        store_embedding(user_id, persona, combined_text, doc_id)
    except Exception as e:
        logger.error(f"Failed to store vector memory: {e}")

    # 3. Persistent chat history (SQLite)
    chat_entry = ChatHistory(
        user_id=user_id,
        persona=persona,
        message=user_message,
        response=ai_response,
    )
    db.add(chat_entry)
    await db.flush()
    logger.debug(f"Stored conversation for user={user_id}, persona={persona}")


async def retrieve_context(
    db: AsyncSession,
    user_id: str,
    persona: str,
    query: str,
) -> dict:
    """
    Retrieve all memory context for the current persona:
    - Recent messages (short-term)
    - Relevant long-term memories (vector search)
    - Persona summary

    STRICT: Only retrieves data for the specified persona.
    """
    # 1. Short-term recent messages
    recent = st_get_recent(user_id, persona, limit=10)

    # 2. Long-term vector memories
    long_term = []
    try:
        long_term = vector_search(
            query=query,
            user_id=user_id,
            persona=persona,
            top_k=settings.LONG_TERM_TOP_K,
        )
    except Exception as e:
        logger.error(f"Vector search failed: {e}")

    # 3. Persona summary
    summary = await get_persona_summary(db, user_id, persona)

    return {
        "recent_messages": recent,
        "long_term_memories": long_term,
        "summary": summary,
    }


async def get_persona_summary(db: AsyncSession, user_id: str, persona: str) -> str | None:
    """Get the stored summary for a user+persona pair."""
    result = await db.execute(
        select(PersonaSummary).where(
            PersonaSummary.user_id == user_id,
            PersonaSummary.persona == persona,
        )
    )
    entry = result.scalar_one_or_none()
    return entry.summary if entry else None


async def update_persona_summary(db: AsyncSession, user_id: str, persona: str, summary: str) -> None:
    """Update or create the summary for a user+persona pair."""
    result = await db.execute(
        select(PersonaSummary).where(
            PersonaSummary.user_id == user_id,
            PersonaSummary.persona == persona,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.summary = summary
    else:
        entry = PersonaSummary(user_id=user_id, persona=persona, summary=summary)
        db.add(entry)
    await db.flush()
    logger.info(f"Updated summary for user={user_id}, persona={persona}")


async def reset_persona_memory(
    db: AsyncSession,
    user_id: str,
    persona: str,
) -> dict:
    """
    Clear ALL memory for a specific user+persona:
    - Short-term (in-memory)
    - Long-term (ChromaDB)
    - Summary (SQLite)
    - Chat history (SQLite)
    """
    # 1. Clear short-term
    st_clear(user_id, persona)

    # 2. Clear long-term vectors
    deleted_vectors = delete_user_persona_memory(user_id, persona)

    # 3. Clear summary
    result = await db.execute(
        select(PersonaSummary).where(
            PersonaSummary.user_id == user_id,
            PersonaSummary.persona == persona,
        )
    )
    summary_entry = result.scalar_one_or_none()
    if summary_entry:
        await db.delete(summary_entry)

    # 4. Clear chat history
    from sqlalchemy import delete
    await db.execute(
        delete(ChatHistory).where(
            ChatHistory.user_id == user_id,
            ChatHistory.persona == persona,
        )
    )
    await db.flush()

    logger.info(f"Reset all memory for user={user_id}, persona={persona}")
    return {
        "user_id": user_id,
        "persona": persona,
        "message": "Memory reset successfully",
        "vectors_deleted": deleted_vectors,
    }


def get_memory_info(user_id: str, persona: str) -> dict:
    """Get memory stats for a user+persona."""
    recent = st_get_recent(user_id, persona)
    lt_count = get_memory_count(user_id, persona)
    return {
        "recent_messages": recent,
        "long_term_count": lt_count,
    }
