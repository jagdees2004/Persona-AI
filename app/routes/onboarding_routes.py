"""
Onboarding routes: global profile + persona-specific preferences.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.schemas import (
    GlobalProfileRequest,
    GlobalProfileResponse,
    PersonaPreferencesRequest,
    PersonaPreferencesResponse,
)
from onboarding.onboarding_service import save_global_profile, save_persona_preferences

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Onboarding"])


@router.post("/onboarding", response_model=GlobalProfileResponse)
async def onboarding(
    request: GlobalProfileRequest,
    db: AsyncSession = Depends(get_db),
):
    """Save or update global user profile (common for all personas)."""
    logger.info(f"Onboarding user: {request.user_id}")
    result = await save_global_profile(db, request.model_dump())
    return GlobalProfileResponse(**result)


@router.post("/persona/setup", response_model=PersonaPreferencesResponse)
async def persona_setup(
    request: PersonaPreferencesRequest,
    db: AsyncSession = Depends(get_db),
):
    """Save persona-specific preferences for a user."""
    logger.info(f"Setting up {request.persona} preferences for user {request.user_id}")
    result = await save_persona_preferences(
        db, request.user_id, request.persona, request.preferences
    )
    return PersonaPreferencesResponse(**result)
