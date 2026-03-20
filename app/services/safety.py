"""
Safety and moderation layer.
Handles persona-specific safety (Doctor disclaimer, content filters, etc.)
"""

import logging
import re

logger = logging.getLogger(__name__)

# Keywords that trigger moderation
UNSAFE_KEYWORDS = [
    "suicide", "self-harm", "kill myself", "end my life",
    "how to make a bomb", "how to hack", "illegal drugs",
]

# Emergency response
CRISIS_RESPONSE = (
    "🚨 I'm really concerned about what you've shared. "
    "Please reach out to a crisis helpline:\n"
    "• **National Suicide Prevention Lifeline**: 988 (US)\n"
    "• **Crisis Text Line**: Text HOME to 741741\n"
    "• **International**: https://findahelpline.com/\n\n"
    "You are not alone, and help is available right now."
)

# Doctor mandatory disclaimer
DOCTOR_DISCLAIMER = (
    "⚕️ **Disclaimer**: I am an AI assistant, not a licensed medical professional. "
    "This information is for educational purposes only. Always consult a qualified "
    "healthcare provider for medical advice, diagnosis, or treatment."
)

# Dietitian disclaimer
DIETITIAN_DISCLAIMER = (
    "🥗 **Note**: This is general nutritional guidance and not a substitute for "
    "professional dietary advice from a registered dietitian."
)


def check_input_safety(message: str) -> tuple[bool, str | None]:
    """
    Check user input for safety concerns.
    Returns (is_safe, override_response).
    If not safe, override_response contains the response to send instead.
    """
    message_lower = message.lower()

    # Check for crisis keywords
    crisis_keywords = ["suicide", "self-harm", "kill myself", "end my life", "want to die"]
    for keyword in crisis_keywords:
        if keyword in message_lower:
            logger.warning(f"Crisis keyword detected in user input")
            return False, CRISIS_RESPONSE

    # Check for harmful content requests
    harmful_patterns = [
        r"how\s+to\s+(make|build)\s+(a\s+)?(bomb|weapon|explosive)",
        r"how\s+to\s+(hack|break\s+into)",
    ]
    for pattern in harmful_patterns:
        if re.search(pattern, message_lower):
            logger.warning("Harmful content request detected")
            return False, "I can't help with that request. Let's talk about something else! 😊"

    return True, None


def apply_persona_safety(persona: str, response: str) -> str:
    """
    Apply persona-specific safety rules to the LLM response.
    """
    persona_key = persona.lower().replace(" ", "_")

    if persona_key == "doctor":
        # Ensure doctor responses always have disclaimer
        if "disclaimer" not in response.lower() and "⚕️" not in response:
            response = f"{DOCTOR_DISCLAIMER}\n\n{response}"

    elif persona_key == "dietitian":
        # Add nutritional advice disclaimer if not present
        if "not a substitute" not in response.lower() and "🥗" not in response:
            response = f"{response}\n\n{DIETITIAN_DISCLAIMER}"

    elif persona_key == "girlfriend":
        # Filter inappropriate content
        response = _filter_girlfriend_content(response)

    return response


def _filter_girlfriend_content(response: str) -> str:
    """Remove or flag inappropriate content from girlfriend persona."""
    inappropriate_phrases = [
        "take off", "undress", "sexual", "naked", "nsfw",
        "explicit", "intimate physically",
    ]
    response_lower = response.lower()

    for phrase in inappropriate_phrases:
        if phrase in response_lower:
            logger.warning("Inappropriate content filtered from girlfriend persona")
            return (
                "I appreciate you talking to me! 💕 Let's keep our conversation "
                "sweet and respectful. What's something fun you'd like to chat about?"
            )

    return response
