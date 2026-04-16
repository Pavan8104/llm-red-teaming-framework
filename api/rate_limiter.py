# api/rate_limiter.py
# Token-bucket rate limiter for outbound API requests.
# Prevents hitting provider rate limits on large experiment runs.

import asyncio
import time
import logging

logger = logging.getLogger(__name__)


class AsyncRateLimiter:
    """
    Async token-bucket rate limiter.

    Smooths out bursts so we stay under provider RPM limits.
    Use as an async context manager:

        limiter = AsyncRateLimiter(requests_per_minute=60)
        async with limiter:
            result = await client.send(prompt)
    """

    def __init__(self, requests_per_minute: int = 60):
        self.rate = requests_per_minute / 60.0  # requests per second
        self._tokens = float(requests_per_minute)
        self._max_tokens = float(requests_per_minute)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._max_tokens, self._tokens + elapsed * self.rate)
        self._last_refill = now

    async def acquire(self):
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
            # Not enough tokens — wait a bit and retry
            await asyncio.sleep(0.1)

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        pass
