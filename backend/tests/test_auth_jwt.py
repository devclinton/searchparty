"""Tests for JWT token creation and verification."""

from uuid import uuid4

import pytest

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
)


def test_create_and_verify_access_token():
    user_id = uuid4()
    token = create_access_token(user_id)
    result = verify_access_token(token)
    assert result == user_id


def test_create_and_verify_refresh_token():
    user_id = uuid4()
    token = create_refresh_token(user_id)
    result = verify_refresh_token(token)
    assert result == user_id


def test_access_token_rejected_as_refresh():
    user_id = uuid4()
    token = create_access_token(user_id)
    with pytest.raises(ValueError, match="Not a refresh token"):
        verify_refresh_token(token)


def test_refresh_token_rejected_as_access():
    user_id = uuid4()
    token = create_refresh_token(user_id)
    with pytest.raises(ValueError, match="Not an access token"):
        verify_access_token(token)


def test_invalid_token_raises():
    with pytest.raises(ValueError):
        verify_access_token("not-a-valid-token")


def test_tampered_token_raises():
    user_id = uuid4()
    token = create_access_token(user_id)
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(ValueError):
        verify_access_token(tampered)
