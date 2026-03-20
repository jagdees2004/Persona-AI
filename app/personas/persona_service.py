"""
Persona service: load config, select, switch, and persist personas.
Uses in-memory cache instead of Redis.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory persona persistence (user_id -> current_persona)
_user_persona_cache: dict[str, str] = {}

# Loaded personas config
_personas_config: dict = {}

DEFAULT_PERSONA = "general_assistant"


def _load_config() -> dict:
    """Load personas from JSON config file."""
    global _personas_config
    if not _personas_config:
        config_path = Path(__file__).parent / "personas_config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            _personas_config = json.load(f)
        logger.info(f"Loaded {len(_personas_config['personas'])} personas from config")
    return _personas_config


def get_all_personas() -> dict:
    """Return all available personas."""
    config = _load_config()
    return config["personas"]


def get_persona(name: str) -> Optional[dict]:
    """Get a single persona by key name."""
    config = _load_config()
    key = name.lower().replace(" ", "_")
    return config["personas"].get(key)


def get_persona_names() -> list[str]:
    """Return list of all persona key names."""
    config = _load_config()
    return list(config["personas"].keys())


def set_user_persona(user_id: str, persona: str) -> str:
    """Set the current persona for a user. Returns the normalized persona key."""
    key = persona.lower().replace(" ", "_")
    if key not in get_persona_names():
        raise ValueError(f"Unknown persona: {persona}. Available: {get_persona_names()}")
    _user_persona_cache[user_id] = key
    logger.info(f"User {user_id} switched to persona: {key}")
    return key


def get_user_persona(user_id: str) -> str:
    """Get the current persona for a user. Defaults to 'general_assistant'."""
    return _user_persona_cache.get(user_id, DEFAULT_PERSONA)


def resolve_persona(user_id: str, requested_persona: Optional[str] = None) -> str:
    """
    Resolve which persona to use:
    1. If persona provided in request → update and use it
    2. If not → use stored persona
    3. Default → 'general_assistant'
    """
    if requested_persona:
        return set_user_persona(user_id, requested_persona)
    return get_user_persona(user_id)
