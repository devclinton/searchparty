"""Tests for password hashing and verification."""

from app.auth.password import hash_password, verify_password


def test_hash_and_verify():
    password = "test-password-123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)


def test_wrong_password_fails():
    hashed = hash_password("correct-password")
    assert not verify_password("wrong-password", hashed)


def test_different_hashes_for_same_password():
    password = "same-password"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2  # bcrypt uses random salt
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)
