"""Tests for auth API endpoints."""

from httpx import AsyncClient

from app.auth.jwt import create_access_token, create_refresh_token

from .conftest import TEST_EMAIL, TEST_PASSWORD, TEST_USER_ID


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


async def test_get_me_authenticated(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
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
