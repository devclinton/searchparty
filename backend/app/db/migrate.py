"""Database migration runner.

Executes SQL migration files in order, skipping already-applied migrations.
Run with: python -m app.db.migrate
"""

import asyncio
import re
from pathlib import Path

import asyncpg

from app.config import settings

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def ensure_migrations_table(conn: asyncpg.Connection) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)


async def get_applied_versions(conn: asyncpg.Connection) -> set[str]:
    rows = await conn.fetch("SELECT version FROM schema_migrations")
    return {row["version"] for row in rows}


def get_migration_files() -> list[tuple[str, Path]]:
    pattern = re.compile(r"^(\d+)_.+\.sql$")
    migrations = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        match = pattern.match(path.name)
        if match:
            migrations.append((match.group(1), path))
    return migrations


async def run_migrations() -> None:
    conn = await asyncpg.connect(dsn=settings.database_url)
    try:
        await ensure_migrations_table(conn)
        applied = await get_applied_versions(conn)
        migrations = get_migration_files()

        for version, path in migrations:
            if version in applied:
                print(f"  skip {path.name} (already applied)")  # noqa: T201
                continue

            print(f"  apply {path.name}...")  # noqa: T201
            sql = path.read_text()
            await conn.execute(sql)
            print(f"  done {path.name}")  # noqa: T201

        print("All migrations applied.")  # noqa: T201
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())
