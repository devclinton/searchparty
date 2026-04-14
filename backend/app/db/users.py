from uuid import UUID

import asyncpg


async def get_user_by_id(pool: asyncpg.Pool, user_id: UUID) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "SELECT * FROM users WHERE id = $1 AND is_active = TRUE",
        user_id,
    )


async def get_user_by_email(pool: asyncpg.Pool, email: str) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "SELECT * FROM users WHERE email = $1 AND is_active = TRUE",
        email,
    )


async def get_user_by_oauth(
    pool: asyncpg.Pool, provider: str, oauth_id: str
) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "SELECT * FROM users WHERE oauth_provider = $1 AND oauth_id = $2 AND is_active = TRUE",
        provider,
        oauth_id,
    )


async def create_user(
    pool: asyncpg.Pool,
    *,
    email: str,
    display_name: str,
    password_hash: str | None = None,
    oauth_provider: str | None = None,
    oauth_id: str | None = None,
    preferred_locale: str = "en",
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO users (email, display_name, password_hash,
            oauth_provider, oauth_id, preferred_locale)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        email,
        display_name,
        password_hash,
        oauth_provider,
        oauth_id,
        preferred_locale,
    )


async def update_user_profile(
    pool: asyncpg.Pool,
    user_id: UUID,
    *,
    display_name: str | None = None,
    contact_phone: str | None = None,
    sar_qualifications: list[str] | None = None,
    preferred_locale: str | None = None,
) -> asyncpg.Record | None:
    # Build dynamic SET clause for only provided fields
    updates = []
    params: list = [user_id]
    idx = 2

    if display_name is not None:
        updates.append(f"display_name = ${idx}")
        params.append(display_name)
        idx += 1
    if contact_phone is not None:
        updates.append(f"contact_phone = ${idx}")
        params.append(contact_phone)
        idx += 1
    if sar_qualifications is not None:
        updates.append(f"sar_qualifications = ${idx}")
        params.append(sar_qualifications)
        idx += 1
    if preferred_locale is not None:
        updates.append(f"preferred_locale = ${idx}")
        params.append(preferred_locale)
        idx += 1

    if not updates:
        return await get_user_by_id(pool, user_id)

    updates.append("updated_at = NOW()")
    set_clause = ", ".join(updates)

    return await pool.fetchrow(
        f"UPDATE users SET {set_clause} WHERE id = $1 AND is_active = TRUE RETURNING *",  # noqa: S608
        *params,
    )


async def deactivate_user(pool: asyncpg.Pool, user_id: UUID) -> bool:
    result = await pool.execute(
        "UPDATE users SET is_active = FALSE, updated_at = NOW() WHERE id = $1",
        user_id,
    )
    return result == "UPDATE 1"
