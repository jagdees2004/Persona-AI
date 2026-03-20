"""
Onboarding service: save global profile and persona-specific preferences.
"""

import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import UserProfile
from models.persona_preferences import PersonaPreferences

logger = logging.getLogger(__name__)


async def save_global_profile(db: AsyncSession, data: dict) -> dict:
    """
    Save or update the global user profile (common across all personas).
    """
    user_id = data["user_id"]

    # Check if user exists
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    existing = result.scalar_one_or_none()

    interests_json = json.dumps(data.get("interests", [])) if data.get("interests") else None

    if existing:
        existing.name = data["name"]
        existing.age = data.get("age")
        existing.gender = data.get("gender")
        existing.location = data.get("location")
        existing.interests = interests_json
        existing.communication_style = data.get("communication_style")
        logger.info(f"Updated global profile for user {user_id}")
    else:
        user = UserProfile(
            user_id=user_id,
            name=data["name"],
            age=data.get("age"),
            gender=data.get("gender"),
            location=data.get("location"),
            interests=interests_json,
            communication_style=data.get("communication_style"),
        )
        db.add(user)
        logger.info(f"Created global profile for user {user_id}")

    await db.flush()
    return {"user_id": user_id, "name": data["name"], "message": "Profile saved successfully"}


async def save_persona_preferences(db: AsyncSession, user_id: str, persona: str, preferences: dict) -> dict:
    """
    Save or update persona-specific preferences for a user.
    """
    persona_key = persona.lower().replace(" ", "_")

    result = await db.execute(
        select(PersonaPreferences).where(
            PersonaPreferences.user_id == user_id,
            PersonaPreferences.persona == persona_key,
        )
    )
    existing = result.scalar_one_or_none()

    prefs_json = json.dumps(preferences)

    if existing:
        existing.preferences = prefs_json
        logger.info(f"Updated {persona_key} preferences for user {user_id}")
    else:
        pref = PersonaPreferences(
            user_id=user_id,
            persona=persona_key,
            preferences=prefs_json,
        )
        db.add(pref)
        logger.info(f"Created {persona_key} preferences for user {user_id}")

    await db.flush()
    return {"user_id": user_id, "persona": persona_key, "message": "Persona preferences saved"}


async def get_global_profile(db: AsyncSession, user_id: str) -> dict | None:
    """Retrieve the global profile for a user."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return None

    return {
        "user_id": user.user_id,
        "name": user.name,
        "age": user.age,
        "gender": user.gender,
        "location": user.location,
        "interests": json.loads(user.interests) if user.interests else [],
        "communication_style": user.communication_style,
    }


async def get_persona_preferences(db: AsyncSession, user_id: str, persona: str) -> dict | None:
    """Retrieve persona-specific preferences for a user."""
    persona_key = persona.lower().replace(" ", "_")
    result = await db.execute(
        select(PersonaPreferences).where(
            PersonaPreferences.user_id == user_id,
            PersonaPreferences.persona == persona_key,
        )
    )
    pref = result.scalar_one_or_none()
    if not pref:
        return None
    return json.loads(pref.preferences)
