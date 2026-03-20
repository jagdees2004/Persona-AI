"""
MongoDB Document Schema: UserProfile

Collection: user_profiles

Document structure:
{
    "_id": "user123",              # Same as user_id (used as primary key)
    "user_id": "user123",
    "name": "John Doe",
    "age": 25,                     # Optional
    "gender": "male",              # Optional
    "location": "India",           # Optional
    "interests": ["AI", "coding"], # Optional, native list
    "communication_style": "casual",  # Optional
    "created_at": datetime,
    "updated_at": datetime
}

Indexes:
- user_id: unique
"""
