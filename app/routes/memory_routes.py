"""
Memory routes: view and reset persona-based memory.
"""

import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.schemas import MemoryResponse, ResetRequest, ResetResponse
from memory.memory_manager import (
    get_memory_info,
    get_persona_summary,
    reset_persona_memory,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Memory"])


@router.get("/memory", response_model=MemoryResponse)
async def get_memory(
    user_id: str = Query(..., description="User ID"),
    persona: str = Query(..., description="Persona name"),
    db: AsyncSession = Depends(get_db),
):
    """Get persona-based memory for a user (short-term + long-term count + summary)."""
    persona_key = persona.lower().replace(" ", "_")

    info = get_memory_info(user_id, persona_key)
    summary = await get_persona_summary(db, user_id, persona_key)

    return MemoryResponse(
        user_id=user_id,
        persona=persona_key,
        recent_messages=info["recent_messages"],
        summary=summary,
        long_term_count=info["long_term_count"],
    )


@router.post("/reset", response_model=ResetResponse)
async def reset_memory(
    request: ResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Clear all memory (short-term, long-term, summary, chat history) for a specific persona."""
    persona_key = request.persona.lower().replace(" ", "_")
    logger.info(f"Resetting memory for user={request.user_id}, persona={persona_key}")

    result = await reset_persona_memory(db, request.user_id, persona_key)
    return ResetResponse(
        user_id=result["user_id"],
        persona=result["persona"],
        message=result["message"],
    )
