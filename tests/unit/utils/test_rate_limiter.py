import asyncio
import time

import pytest

from crypto_bot.utils.rate_limiter import AsyncTokenBucket, ConcurrencyGuard


@pytest.mark.asyncio
async def test_token_bucket_rate():
    bucket = AsyncTokenBucket(rate_per_sec=5, capacity=5)
    start = time.monotonic()
    for _ in range(7):
        await bucket.acquire()
    elapsed = time.monotonic() - start
    # 7 tokens at 5/sec: at least ~0.2s in typical CI (timing can vary)
    assert elapsed >= 0.18


@pytest.mark.asyncio
async def test_concurrency_guard_limits():
    guard = ConcurrencyGuard(max_in_flight=2)
    in_flight = 0

    async def task():
        nonlocal in_flight
        async with guard.limit():
            in_flight += 1
            await asyncio.sleep(0.05)
            assert in_flight <= 2
            in_flight -= 1

    await asyncio.gather(*(task() for _ in range(5)))
