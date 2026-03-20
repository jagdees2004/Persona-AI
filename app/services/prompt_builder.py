"""
Prompt Builder: assembles the full prompt using persona-aware context.

STRICT RULE: Only uses memory from the currently selected persona.

Prompt structure:
1. Persona System Instructions
2. Global User Profile 
3. Persona-Specific Preferences
4. Persona-Specific Summary
5. Retrieved Long-Term Memories
6. Recent Short-Term Messages
7. Current User Input
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def build_prompt(
    persona_config: dict,
    user_profile: dict | None,
    persona_preferences: dict | None,
    memory_context: dict,
    user_message: str,
) -> list[dict]:
    """
    Build the complete prompt array for the LLM chat completion API.
    All context is already filtered to the current persona.
    """
    system_parts = []

    # 1. System Instructions
    system_prompt = persona_config.get("system_prompt", "You are a helpful AI assistant.")
    tone = persona_config.get("tone", "")
    response_style = persona_config.get("response_style", "")
    behavior_rules = persona_config.get("behavior_rules", [])
    safety_constraints = persona_config.get("safety_constraints", [])

    system_parts.append(system_prompt)
    if tone: system_parts.append(f"\nTone: {tone}")
    if response_style: system_parts.append(f"\nResponse Style: {response_style}")

    if behavior_rules:
        system_parts.append("\n\nBehavior Rules:")
        for rule in behavior_rules:
            system_parts.append(f"\n- {rule}")

    if safety_constraints:
        system_parts.append("\n\nSafety Constraints:")
        for constraint in safety_constraints:
            system_parts.append(f"\n- {constraint}")

    # 2. Global User Profile
    if user_profile:
        system_parts.append("\n\n--- User Profile ---")
        system_parts.append(f"\nName: {user_profile.get('name', 'Unknown')}")
        if user_profile.get('age'):
            system_parts.append(f"\nAge: {user_profile['age']}")
        if user_profile.get('gender'):
            system_parts.append(f"\nGender: {user_profile['gender']}")
        if user_profile.get('location'):
            system_parts.append(f"\nLocation: {user_profile['location']}")
        if user_profile.get('interests') and isinstance(user_profile['interests'], list):
            system_parts.append(f"\nInterests: {', '.join(user_profile['interests'])}")
        if user_profile.get('communication_style'):
            system_parts.append(f"\nPreferred Communication: {user_profile['communication_style']}")

    # 3. Persona-Specific Preferences
    if persona_preferences:
        system_parts.append("\n\n--- User Preferences (for this persona) ---")
        for key, value in persona_preferences.items():
            system_parts.append(f"\n{key}: {value}")

    # 4. Persona-Specific Summary
    summary = memory_context.get("summary")
    if summary:
        system_parts.append(f"\n\n--- Conversation Summary ---\n{summary}")

    # 5. Retrieved Long-Term Memories
    long_term = memory_context.get("long_term_memories", [])
    if long_term:
        system_parts.append("\n\n--- Relevant Past Conversations ---")
        for mem in long_term[:5]:
            system_parts.append(f"\n{mem['text']}")

    messages = [{"role": "system", "content": "".join(system_parts)}]

    # 6. Recent Messages (Short-Term)
    recent = memory_context.get("recent_messages", [])
    for msg in recent[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        # Safely constrain to typical roles if necessary; default Llama handles user/assistant
        messages.append({"role": role, "content": content})

    # 7. Current User Input
    messages.append({"role": "user", "content": user_message})

    logger.debug(f"Built prompt array (system msg: {len(messages[0]['content'])} chars) for persona: {persona_config.get('name', 'unknown')}")
    return messages


def estimate_tokens(text: str) -> int:
    """Rough token estimation (~4 chars per token for English)."""
    return len(text) // 4
