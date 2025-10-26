"""
Test rate limiter with actual threads to verify thread-safety.
"""

import asyncio
import threading
import time

from rate_limiter import rate_limit


def test_rate_limit_across_threads():
    """Test that rate limiter works correctly across multiple threads."""
    call_times = []
    lock = threading.Lock()

    @rate_limit(calls=2, period=1)
    async def tracked_call(n: int, thread_id: int):
        with lock:
            call_times.append((thread_id, n, time.monotonic()))
        await asyncio.sleep(0.01)  # Simulate work
        return n

    def run_in_thread(thread_id: int):
        """Run async function in a thread."""

        async def thread_main():
            # Make 3 calls from this thread
            for i in range(3):
                await tracked_call(i, thread_id)

        asyncio.run(thread_main())

    # Create and start 3 threads
    start = time.monotonic()
    threads = []
    for i in range(3):
        thread = threading.Thread(target=run_in_thread, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    elapsed = time.monotonic() - start

    # We have 9 total calls (3 threads x 3 calls each)
    # With 2 calls/sec (0.5s spacing), this should take ~4 seconds
    print(f"\n9 calls across 3 threads took {elapsed:.2f}s")
    print(f"Expected: ~4.0s (with 0.5s spacing for 9 calls)")

    # Sort by time to see actual ordering
    call_times.sort(key=lambda x: x[2])

    print("\nCall order:")
    prev_time = None
    for thread_id, call_n, call_time in call_times:
        relative_time = call_time - call_times[0][2]
        if prev_time:
            gap = (call_time - prev_time) * 1000
            print(
                f"  Thread {thread_id}, Call {call_n}: {relative_time:.3f}s (gap: {gap:.0f}ms)"
            )
        else:
            print(f"  Thread {thread_id}, Call {call_n}: {relative_time:.3f}s")
        prev_time = call_time

    # Verify timing
    assert 3.8 <= elapsed <= 4.5, f"Expected ~4.0s, got {elapsed:.2f}s"

    # Verify spacing between calls
    for i in range(1, len(call_times)):
        gap = call_times[i][2] - call_times[i - 1][2]
        # Each gap should be ~0.5s (with some tolerance)
        assert 0.45 <= gap <= 0.55, f"Gap {i} was {gap:.3f}s, expected ~0.5s"

    print("\n✅ Rate limiter correctly enforced across threads!")


if __name__ == "__main__":
    test_rate_limit_across_threads()
