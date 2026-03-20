"""Script to view all chat history from MongoDB Atlas."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import get_settings

async def view_history():
    settings = get_settings()
    print(f"Connecting to: {settings.MONGODB_DB_NAME}...")
    
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    
    # Fetch all chats
    chats = await db.chat_history.find().sort("timestamp", 1).to_list(100)
    
    if not chats:
        print("No chat history found.")
        return

    print(f"\n--- Found {len(chats)} messages ---\n")
    for chat in chats:
        ts = chat.get("timestamp", "N/A")
        user = chat.get("user_id", "N/A")
        persona = chat.get("persona", "N/A")
        msg = chat.get("message", "")
        resp = chat.get("response", "")
        
        print(f"[{ts}] {user} (as {persona}):")
        print(f"  > {msg}")
        print(f"  🤖 {resp}")
        print("-" * 40)

    client.close()

if __name__ == "__main__":
    asyncio.run(view_history())
