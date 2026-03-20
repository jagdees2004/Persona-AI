"""
Persona routes: list personas, get persona info.
"""

import logging
from fastapi import APIRouter
from models.schemas import PersonaInfo, PersonaListResponse
from personas.persona_service import get_all_personas

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Personas"])


@router.get("/personas", response_model=PersonaListResponse)
async def list_personas():
    """List all available AI personas."""
    personas = get_all_personas()
    persona_list = []
    for key, config in personas.items():
        persona_list.append(PersonaInfo(
            name=config["name"],
            description=config["description"],
            tone=config["tone"],
            response_style=config["response_style"],
            persona_specific_fields=config.get("persona_specific_fields", []),
        ))
    return PersonaListResponse(personas=persona_list)
