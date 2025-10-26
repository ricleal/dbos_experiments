"""
Test suite for the async rate limiter decorator.
"""

import asyncio
import time

import pytest
from rate_limiter import rate_limit


@pytest.mark.asyncio
async def test_rate_limit_spacing():
    """Test that calls are evenly spaced."""
    call_times = []

    @rate_limit(calls=2, period=1)
    async def tracked_call():
        call_times.append(time.monotonic())
        return "done"

    # Make 5 calls
    start = time.monotonic()
    for _ in range(5):
        await tracked_call()
    elapsed = time.monotonic() - start

    # Should take approximately 2 seconds (5 calls at 0.5s spacing = 2s)
    assert 1.9 <= elapsed <= 2.2, f"Expected ~2.0s, got {elapsed:.2f}s"

    # Check spacing between calls
    for i in range(1, len(call_times)):
        interval = call_times[i] - call_times[i - 1]
        # Each interval should be ~0.5 seconds
        assert 0.45 <= interval <= 0.55, f"Expected ~0.5s spacing, got {interval:.2f}s"


@pytest.mark.asyncio
async def test_rate_limit_concurrent():
    """Test that concurrent calls are properly serialized."""
    call_times = []

    @rate_limit(calls=2, period=1)
    async def tracked_call(n: int):
        call_times.append((n, time.monotonic()))
        await asyncio.sleep(0.01)  # Simulate some work
        return n

    # Launch all calls concurrently
    start = time.monotonic()
    results = await asyncio.gather(*[tracked_call(i) for i in range(4)])
    elapsed = time.monotonic() - start

    # Should take approximately 1.5 seconds (4 calls at 0.5s spacing)
    assert 1.4 <= elapsed <= 1.7, f"Expected ~1.5s, got {elapsed:.2f}s"

    # Results should be in order
    assert results == [0, 1, 2, 3]

    # Calls should be in order and properly spaced
    for i in range(1, len(call_times)):
        interval = call_times[i][1] - call_times[i - 1][1]
        assert 0.45 <= interval <= 0.55, f"Expected ~0.5s spacing, got {interval:.2f}s"


@pytest.mark.asyncio
async def test_rate_limit_burst_then_pause():
    """Test that rate limiter handles bursts followed by pauses."""
    call_times = []

    @rate_limit(calls=2, period=1)
    async def tracked_call():
        call_times.append(time.monotonic())
        return "done"

    # Make 3 calls quickly
    for _ in range(3):
        await tracked_call()

    # Wait 2 seconds
    await asyncio.sleep(2)

    # Make 2 more calls - should be immediate since we waited
    before_pause = time.monotonic()
    for _ in range(2):
        await tracked_call()
    after_pause = time.monotonic()

    # The last 2 calls should still be spaced 0.5s apart
    pause_duration = after_pause - before_pause
    assert 0.45 <= pause_duration <= 0.55, f"Expected ~0.5s, got {pause_duration:.2f}s"


@pytest.mark.asyncio
async def test_different_rate_limits():
    """Test different rate limit configurations."""

    @rate_limit(calls=5, period=1)
    async def fast_call():
        return time.monotonic()

    @rate_limit(calls=1, period=1)
    async def slow_call():
        return time.monotonic()

    # Fast: 5 calls should take ~0.8s (0.2s spacing)
    start = time.monotonic()
    for _ in range(5):
        await fast_call()
    fast_elapsed = time.monotonic() - start
    assert 0.7 <= fast_elapsed <= 1.0, f"Expected ~0.8s, got {fast_elapsed:.2f}s"

    # Slow: 3 calls should take ~2s (1s spacing)
    start = time.monotonic()
    for _ in range(3):
        await slow_call()
    slow_elapsed = time.monotonic() - start
    assert 1.9 <= slow_elapsed <= 2.2, f"Expected ~2.0s, got {slow_elapsed:.2f}s"


@pytest.mark.asyncio
async def test_rate_limit_with_arguments():
    """Test that rate limiter works with function arguments."""
    results = []

    @rate_limit(calls=2, period=1)
    async def process_item(item: str, multiplier: int = 2):
        results.append((item, multiplier))
        return item * multiplier

    # Call with various arguments
    r1 = await process_item("a", 3)
    r2 = await process_item("b")
    r3 = await process_item("c", 1)

    assert r1 == "aaa"
    assert r2 == "bb"
    assert r3 == "c"
    assert results == [("a", 3), ("b", 2), ("c", 1)]


if __name__ == "__main__":
    # Run tests manually
    asyncio.run(test_rate_limit_spacing())
    print("✓ test_rate_limit_spacing passed")

    asyncio.run(test_rate_limit_concurrent())
    print("✓ test_rate_limit_concurrent passed")

    asyncio.run(test_rate_limit_burst_then_pause())
    print("✓ test_rate_limit_burst_then_pause passed")

    asyncio.run(test_different_rate_limits())
    print("✓ test_different_rate_limits passed")

    asyncio.run(test_rate_limit_with_arguments())
    print("✓ test_rate_limit_with_arguments passed")

    print("\nAll tests passed! ✨")
