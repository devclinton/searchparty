"""Tests for the rate limiter."""

import pytest
from fastapi import HTTPException

from app.auth.rate_limit import RateLimiter


class FakeRequest:
    def __init__(self, ip: str = "127.0.0.1"):
        self.client = type("Client", (), {"host": ip})()
        self.headers = {}


def test_allows_under_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    req = FakeRequest()
    limiter.check(req)
    limiter.check(req)
    limiter.check(req)
    # 3 requests should all succeed


def test_blocks_over_limit():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    req = FakeRequest()
    limiter.check(req)
    limiter.check(req)
    with pytest.raises(HTTPException) as exc_info:
        limiter.check(req)
    assert exc_info.value.status_code == 429


def test_different_ips_independent():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    req1 = FakeRequest("10.0.0.1")
    req2 = FakeRequest("10.0.0.2")
    limiter.check(req1)
    limiter.check(req2)
    # Both should succeed — different IPs


def test_respects_x_forwarded_for():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    req = FakeRequest()
    req.headers = {"x-forwarded-for": "1.2.3.4, 5.6.7.8"}
    limiter.check(req)
    with pytest.raises(HTTPException):
        limiter.check(req)
