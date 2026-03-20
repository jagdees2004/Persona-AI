"""
MongoDB Document Schema: PersonaSummary

Collection: persona_summaries

Document structure:
{
    "_id": ObjectId,
    "user_id": "user123",
    "persona": "mentor",
    "summary": "User is learning Python and interested in AI...",
    "updated_at": datetime
}

Indexes:
- (user_id, persona): unique compound index
"""
