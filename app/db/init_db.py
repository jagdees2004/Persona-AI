"""
Database initialization script.
Creates all tables defined in SQLAlchemy models.
"""

import asyncio
from core.database import init_db


async def main():
    print("Creating database tables...")
    await init_db()
    print("✅ Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(main())
