"""
Simple async rate limiter utilities.

Provides token bucket and in-flight semaphores to protect external APIs.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator


class AsyncTokenBucket:
    def __init__(self, rate_per_sec: float, capacity: int | None = None) -> None:
        self.rate = rate_per_sec
        self.capacity = capacity or max(1, int(rate_per_sec))
        self.tokens = float(self.capacity)
        self.updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.updated_at
            self.updated_at = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            if self.tokens < 1:
                # Need to wait for next token
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = max(0.0, self.tokens + wait_time * self.rate)
            self.tokens -= 1


class ConcurrencyGuard:
    def __init__(self, max_in_flight: int) -> None:
        self._sem = asyncio.Semaphore(max(1, max_in_flight))

    @asynccontextmanager
    async def limit(self) -> AsyncIterator[None]:
        await self._sem.acquire()
        try:
            yield
        finally:
            self._sem.release()
