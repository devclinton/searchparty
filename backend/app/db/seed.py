"""Database seed script for local testing.

Run with: python -m app.db.seed
"""

import asyncio

import asyncpg

from app.config import settings


async def seed_data() -> None:
    conn = await asyncpg.connect(dsn=settings.database_url)
    try:
        # Check if seed data already exists
        count = await conn.fetchval("SELECT COUNT(*) FROM users")
        if count > 0:
            print("Seed data already exists, skipping.")  # noqa: T201
            return

        # Create test users
        await conn.execute("""
            INSERT INTO users (email, display_name, password_hash, preferred_locale)
            VALUES
                ('commander@example.com', 'IC Commander', '$placeholder', 'en'),
                ('ops@example.com', 'Ops Chief', '$placeholder', 'en'),
                ('leader1@example.com', 'Team Leader Alpha', '$placeholder', 'en'),
                ('leader2@example.com', 'Team Leader Bravo', '$placeholder', 'en'),
                ('searcher1@example.com', 'Searcher One', '$placeholder', 'en'),
                ('searcher2@example.com', 'Searcher Two', '$placeholder', 'es'),
                ('searcher3@example.com', 'Searcher Three', '$placeholder', 'fr')
        """)

        print("Seed data inserted successfully.")  # noqa: T201
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed_data())
