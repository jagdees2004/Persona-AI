"""
Memory Manager: orchestrates short-term + long-term memory.
Ensures strict persona isolation — ONLY accesses the current persona's memory.

Uses MongoDB for persistent storage and ChromaDB for vector search.
"""

import logging
import uuid
from datetime import datetime, timezone

from memory.short_term_memory import (
    add_message as st_add,
    add_message_persistent as st_add_persistent,
    get_recent as st_get_recent,
    clear as st_clear,
    clear_persistent as st_clear_persistent,
    load_from_db as st_load_from_db,
)
from memory.vector_memory import (
    store_embedding,
    search as vector_search,
    delete_user_persona_memory,
    get_memory_count,
)
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def store_conversation(
    db,
    user_id: str,
    persona: str,
    user_message: str,
    ai_response: str,
) -> None:
    """
    Store a conversation turn in all memory layers:
    1. Short-term (in-memory + MongoDB)
    2. Long-term (ChromaDB vector store)
    3. Persistent (MongoDB chat_history)
    """
    # 1. Short-term memory (with MongoDB persistence)
    await st_add_persistent(db, user_id, persona, "user", user_message)
    await st_add_persistent(db, user_id, persona, "assistant", ai_response)

    # 2. Long-term vector memory — store the exchange as a single document
    doc_id = f"{user_id}_{persona}_{uuid.uuid4().hex[:12]}"
    combined_text = f"User: {user_message}\nAssistant: {ai_response}"
    try:
        store_embedding(user_id, persona, combined_text, doc_id)
    except Exception as e:
        logger.error(f"Failed to store vector memory: {e}")

    # 3. Persistent chat history (MongoDB)
    try:
        await db.chat_history.insert_one({
            "user_id": user_id,
            "persona": persona,
            "message": user_message,
            "response": ai_response,
            "timestamp": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.error(f"Failed to store chat history: {e}")

    logger.debug(f"Stored conversation for user={user_id}, persona={persona}")


async def retrieve_context(
    db,
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
    # Load short-term from MongoDB if not in memory
    await st_load_from_db(db, user_id, persona)

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


async def get_persona_summary(db, user_id: str, persona: str) -> str | None:
    """Get the stored summary for a user+persona pair."""
    doc = await db.persona_summaries.find_one(
        {"user_id": user_id, "persona": persona},
        {"_id": 0, "summary": 1},
    )
    return doc["summary"] if doc else None


async def update_persona_summary(db, user_id: str, persona: str, summary: str) -> None:
    """Update or create the summary for a user+persona pair."""
    await db.persona_summaries.update_one(
        {"user_id": user_id, "persona": persona},
        {
            "$set": {
                "summary": summary,
                "updated_at": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "user_id": user_id,
                "persona": persona,
            },
        },
        upsert=True,
    )
    logger.info(f"Updated summary for user={user_id}, persona={persona}")


async def reset_persona_memory(
    db,
    user_id: str,
    persona: str,
) -> dict:
    """
    Clear ALL memory for a specific user+persona:
    - Short-term (in-memory + MongoDB)
    - Long-term (ChromaDB)
    - Summary (MongoDB)
    - Chat history (MongoDB)
    """
    # 1. Clear short-term (in-memory + MongoDB)
    await st_clear_persistent(db, user_id, persona)

    # 2. Clear long-term vectors (ChromaDB)
    deleted_vectors = delete_user_persona_memory(user_id, persona)

    # 3. Clear summary
    await db.persona_summaries.delete_many({
        "user_id": user_id,
        "persona": persona,
    })

    # 4. Clear chat history
    await db.chat_history.delete_many({
        "user_id": user_id,
        "persona": persona,
    })

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
