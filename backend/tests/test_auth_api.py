"""Tests for auth API endpoints.

Uses dependency overrides to mock the database pool, allowing tests
to run without a live PostgreSQL instance.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.jwt import create_access_token, create_refresh_token
from app.auth.password import hash_password
from app.db.connection import get_pool
from app.main import app

TEST_USER_ID = uuid4()
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "secure-password-123"
TEST_HASH = hash_password(TEST_PASSWORD)


def make_user_record(
    user_id=TEST_USER_ID,
    email=TEST_EMAIL,
    password_hash=TEST_HASH,
    display_name="Test User",
):
    """Create a dict that mimics an asyncpg Record."""
    return {
        "id": user_id,
        "email": email,
        "display_name": display_name,
        "password_hash": password_hash,
        "oauth_provider": None,
        "oauth_id": None,
        "contact_phone": None,
        "sar_qualifications": [],
        "preferred_locale": "en",
        "is_active": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


class FakePool:
    """Mock asyncpg pool that routes queries to test data."""

    def __init__(self):
        self.users = {}

    async def fetchrow(self, query, *args):
        query_lower = query.strip().lower()
        if "from users where id" in query_lower:
            return self.users.get(str(args[0]))
        if "from users where email" in query_lower:
            for u in self.users.values():
                if u["email"] == args[0]:
                    return u
            return None
        if "insert into users" in query_lower:
            user = make_user_record(
                user_id=uuid4(),
                email=args[0],
                password_hash=args[2],
                display_name=args[1],
            )
            self.users[str(user["id"])] = user
            return user
        return None

    async def fetch(self, query, *args):
        return []

    async def execute(self, query, *args):
        return "UPDATE 1"


@pytest.fixture
def fake_pool():
    pool = FakePool()
    pool.users[str(TEST_USER_ID)] = make_user_record()
    return pool


@pytest.fixture
async def client(fake_pool):
    async def override_get_pool():
        return fake_pool

    app.dependency_overrides[get_pool] = override_get_pool
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_register_success(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "password123",
            "display_name": "New User",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["display_name"] == "New User"


async def test_register_duplicate_email(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": "password123",
            "display_name": "Duplicate",
        },
    )
    assert resp.status_code == 409


async def test_register_short_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "short@example.com",
            "password": "short",
            "display_name": "Short Pass",
        },
    )
    assert resp.status_code == 422


async def test_login_success(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": "wrong-password"},
    )
    assert resp.status_code == 401


async def test_login_nonexistent_email(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert resp.status_code == 401


async def test_refresh_token_success(client: AsyncClient):
    refresh = create_refresh_token(TEST_USER_ID)
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_refresh_with_access_token_fails(client: AsyncClient):
    access = create_access_token(TEST_USER_ID)
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access},
    )
    assert resp.status_code == 401


async def test_get_me_authenticated(client: AsyncClient):
    token = create_access_token(TEST_USER_ID)
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == TEST_EMAIL


async def test_get_me_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


async def test_get_me_invalid_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert resp.status_code == 401
