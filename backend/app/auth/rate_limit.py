"""Simple in-memory rate limiter for auth endpoints.

Uses a sliding window approach. For production with multiple instances,
replace with Redis-based rate limiting.
"""

import time
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        return client.host if client else "unknown"

    def _cleanup(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def check(self, request: Request) -> None:
        key = self._get_key(request)
        self._cleanup(key)

        if len(self._requests[key]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

        self._requests[key].append(time.monotonic())


# Auth rate limiters
auth_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
register_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)


def rate_limit(limiter: RateLimiter) -> Callable[..., Coroutine[Any, Any, None]]:
    async def dependency(request: Request) -> None:
        limiter.check(request)

    return dependency
