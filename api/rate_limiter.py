# api/rate_limiter.py — token-bucket rate limiter for outbound API requests
# large experiment runs mein provider rate limits hit hone se bachata hai
# bursts smooth karta hai taaki hum RPM limits ke andar rahein

import asyncio
import time
import logging

logger = logging.getLogger(__name__)


class AsyncRateLimiter:
    """
    Async token-bucket rate limiter.

    Bursts smooth karta hai taaki provider ke RPM limits ke andar rahein.
    Async context manager ke taur pe use karo:

        limiter = AsyncRateLimiter(requests_per_minute=60)
        async with limiter:
            result = await client.send(prompt)
    """

    def __init__(self, requests_per_minute: int = 60):
        # requests per second mein convert karo — internal rate
        self.rate         = requests_per_minute / 60.0
        self._tokens      = float(requests_per_minute)
        self._max_tokens  = float(requests_per_minute)
        self._last_refill = time.monotonic()
        self._lock        = asyncio.Lock()

    def _refill(self):
        # elapsed time ke basis pe tokens add karo
        # max_tokens se zyada nahi ho sakta
        now            = time.monotonic()
        elapsed        = now - self._last_refill
        self._tokens   = min(self._max_tokens, self._tokens + elapsed * self.rate)
        self._last_refill = now

    async def acquire(self):
        # ek token acquire karo — agar available nahi to wait karo
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
            # tokens nahi hain — thoda ruko aur dobara check karo
            await asyncio.sleep(0.1)

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        pass  # release karne ki zaroorat nahi — token bucket self-refilling hai
