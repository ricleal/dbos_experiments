"""
Generic async rate limiter decorator for Python.

This module provides a rate limiting decorator that evenly spaces function calls
over time, ensuring compliance with rate limits while maximizing throughput.

Usage:
    from rate_limiter import rate_limit

    @rate_limit(calls=2, period=1)  # 2 calls per second, spaced 0.5s apart
    async def my_api_call():
        # Your async code here
        pass
"""

import asyncio
import threading
import time
from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def rate_limit(calls: int, period: float) -> Callable[[F], F]:
    """
    Async rate limiter decorator that evenly spaces calls over time.

    This decorator ensures that calls to the decorated function are evenly
    distributed over the specified time period, preventing bursts and ensuring
    compliance with rate limits.

    Args:
        calls: Maximum number of calls allowed in the period
        period: Time period in seconds

    Returns:
        Decorated function that enforces the rate limit

    Example:
        @rate_limit(calls=10, period=60)  # 10 calls per minute
        async def fetch_data():
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.example.com/data")
                return response.json()

        # Calls will be spaced 6 seconds apart (60s / 10 calls)
        for i in range(20):
            data = await fetch_data()

    Note:
        - Uses threading.Lock to ensure thread-safety across multiple threads and event loops
        - Works correctly with asyncio in single or multi-threaded contexts
        - Tracks timing using time.monotonic() for accuracy
        - Calculates minimum interval as period / calls
        - Automatically sleeps to maintain even spacing
    """
    min_interval = period / calls

    def decorator(func: F) -> F:
        next_allowed_time = None
        lock = threading.Lock()

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal next_allowed_time

            # Calculate wait time inside lock
            with lock:
                current_time = time.monotonic()

                if next_allowed_time is not None:
                    # Wait until the next allowed time
                    wait_time = max(0, next_allowed_time - current_time)
                    # Schedule next call min_interval after the reserved time
                    next_allowed_time = next_allowed_time + min_interval
                else:
                    # First call - no wait needed
                    wait_time = 0
                    next_allowed_time = current_time + min_interval

            # Sleep outside the lock if needed
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            return await func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


# Example usage
if __name__ == "__main__":
    import httpx

    async def main():
        print("Starting rate-limited calls (2 per second)...")
        start = time.time()

        @rate_limit(calls=2, period=1)
        async def test_api_call(n: int) -> str:
            """Test function that simulates an API call."""
            elapsed = time.time() - start
            print(f"Call {n} at {elapsed:.3f}s")
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://jsonplaceholder.typicode.com/users/1"
                )
                return response.json()

        # Make 10 calls - should take ~4.5 seconds (0.5s spacing)
        tasks = [test_api_call(i) for i in range(10)]
        await asyncio.gather(*tasks)

        elapsed = time.time() - start
        print(f"\nCompleted 10 calls in {elapsed:.2f} seconds")
        print("Expected: ~4.5 seconds (with 0.5s spacing)")

    asyncio.run(main())
