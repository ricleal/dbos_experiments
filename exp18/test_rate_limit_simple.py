"""Simple test to verify rate limiter works with 4 calls/sec"""

import asyncio
import time

from rate_limiter import rate_limit


@rate_limit(calls=4, period=1)
async def dummy_call(n):
    """Fast dummy function - no actual API call"""
    return f"result_{n}"


async def main():
    start = time.monotonic()
    entry_times = []

    for i in range(1, 21):
        entry_time = time.monotonic()
        result = await dummy_call(i)
        entry_times.append((i, entry_time - start))

    print("\nCall timing:")
    print("=" * 50)
    prev_time = 0
    for call_num, elapsed in entry_times:
        gap = (elapsed - prev_time) * 1000
        if call_num > 1:
            print(f"Call {call_num:2d}: {elapsed:6.3f}s (gap: {gap:5.0f}ms)")
        else:
            print(f"Call {call_num:2d}: {elapsed:6.3f}s")
        prev_time = elapsed

    print("\nExpected: 250ms between each call")
    print("All gaps should be ~250ms (±2ms for timing precision)")


if __name__ == "__main__":
    asyncio.run(main())
