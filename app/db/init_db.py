"""
Database initialization script.
Creates MongoDB indexes for all collections.
"""

import asyncio
from core.database import init_db, close_db


async def main():
    print("Creating MongoDB indexes...")
    await init_db()
    print("✅ MongoDB indexes created successfully!")
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
