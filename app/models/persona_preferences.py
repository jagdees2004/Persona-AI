"""
MongoDB Document Schema: PersonaPreferences

Collection: persona_preferences

Document structure:
{
    "_id": ObjectId,
    "user_id": "user123",
    "persona": "dietitian",
    "preferences": {               # Native dict — no JSON serialization needed
        "diet_type": "vegetarian",
        "allergies": ["peanuts"]
    },
    "updated_at": datetime
}

Indexes:
- (user_id, persona): unique compound index
"""
