"""
Onboarding service: save global profile and persona-specific preferences.
Uses MongoDB for persistence.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def save_global_profile(db, data: dict) -> dict:
    """
    Save or update the global user profile (common across all personas).
    Uses MongoDB upsert for atomic create-or-update.
    """
    user_id = data["user_id"]
    now = datetime.now(timezone.utc)

    update_doc = {
        "$set": {
            "name": data["name"],
            "age": data.get("age"),
            "gender": data.get("gender"),
            "location": data.get("location"),
            "interests": data.get("interests", []),
            "communication_style": data.get("communication_style"),
            "updated_at": now,
        },
        "$setOnInsert": {
            "user_id": user_id,
            "created_at": now,
        },
    }

    await db.user_profiles.update_one(
        {"user_id": user_id},
        update_doc,
        upsert=True,
    )

    logger.info(f"Saved global profile for user {user_id}")
    return {"user_id": user_id, "name": data["name"], "message": "Profile saved successfully"}


async def save_persona_preferences(db, user_id: str, persona: str, preferences: dict) -> dict:
    """
    Save or update persona-specific preferences for a user.
    Uses MongoDB upsert for atomic create-or-update.
    """
    persona_key = persona.lower().replace(" ", "_")
    now = datetime.now(timezone.utc)

    await db.persona_preferences.update_one(
        {"user_id": user_id, "persona": persona_key},
        {
            "$set": {
                "preferences": preferences,  # Native dict — no JSON serialization needed
                "updated_at": now,
            },
            "$setOnInsert": {
                "user_id": user_id,
                "persona": persona_key,
            },
        },
        upsert=True,
    )

    logger.info(f"Saved {persona_key} preferences for user {user_id}")
    return {"user_id": user_id, "persona": persona_key, "message": "Persona preferences saved"}


async def get_global_profile(db, user_id: str) -> dict | None:
    """Retrieve the global profile for a user."""
    doc = await db.user_profiles.find_one(
        {"user_id": user_id},
        {"_id": 0},  # Exclude MongoDB's internal _id
    )
    if not doc:
        return None

    return {
        "user_id": doc.get("user_id"),
        "name": doc.get("name"),
        "age": doc.get("age"),
        "gender": doc.get("gender"),
        "location": doc.get("location"),
        "interests": doc.get("interests", []),
        "communication_style": doc.get("communication_style"),
    }


async def get_persona_preferences(db, user_id: str, persona: str) -> dict | None:
    """Retrieve persona-specific preferences for a user."""
    persona_key = persona.lower().replace(" ", "_")
    doc = await db.persona_preferences.find_one(
        {"user_id": user_id, "persona": persona_key},
        {"_id": 0, "preferences": 1},
    )
    if not doc:
        return None
    return doc.get("preferences", {})
