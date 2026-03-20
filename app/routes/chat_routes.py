"""
Chat route: main conversation endpoint with persona switching and memory.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.schemas import ChatRequest, ChatResponse
from personas.persona_service import resolve_persona, get_persona
from onboarding.onboarding_service import get_global_profile, get_persona_preferences
from memory.memory_manager import store_conversation, retrieve_context
from services.prompt_builder import build_prompt
from services.llm_service import generate_response
from services.safety import check_input_safety, apply_persona_safety

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Main chat endpoint.
    - Resolves persona (switch if provided, else use stored)
    - Retrieves persona-isolated memory context
    - Builds prompt with all context layers
    - Calls LLM
    - Applies safety filters
    - Stores conversation in all memory layers
    """
    user_id = request.user_id
    message = request.message

    # 1. Safety check on input
    is_safe, override = check_input_safety(message)
    if not is_safe:
        return ChatResponse(
            user_id=user_id,
            persona="system",
            message=message,
            response=override,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # 2. Resolve persona
    try:
        persona = resolve_persona(user_id, request.persona)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    persona_config = get_persona(persona)
    if not persona_config:
        raise HTTPException(status_code=404, detail=f"Persona '{persona}' not found")

    # 3. Retrieve persona-isolated memory context
    memory_context = await retrieve_context(db, user_id, persona, message)

    # 4. Get user profile and persona preferences
    user_profile = await get_global_profile(db, user_id)
    persona_prefs = await get_persona_preferences(db, user_id, persona)

    # 5. Build prompt
    prompt = build_prompt(
        persona_config=persona_config,
        user_profile=user_profile,
        persona_preferences=persona_prefs,
        memory_context=memory_context,
        user_message=message,
    )

    # 6. Call LLM
    try:
        ai_response = await generate_response(prompt)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        ai_response = "I'm having trouble responding right now. Please try again."

    # 7. Apply persona-specific safety
    ai_response = apply_persona_safety(persona, ai_response)

    # 8. Store conversation in all memory layers
    await store_conversation(db, user_id, persona, message, ai_response)

    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info(f"Chat completed: user={user_id}, persona={persona}")

    return ChatResponse(
        user_id=user_id,
        persona=persona,
        message=message,
        response=ai_response,
        timestamp=timestamp,
    )
