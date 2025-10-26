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
        - Uses asyncio.Lock to ensure thread-safety in async contexts
        - Tracks timing using time.monotonic() for accuracy
        - Calculates minimum interval as period / calls
        - Automatically sleeps to maintain even spacing
    """
    min_interval = period / calls

    def decorator(func: F) -> F:
        last_call_time = None
        lock = asyncio.Lock()

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal last_call_time

            async with lock:
                current_time = time.monotonic()

                if last_call_time is not None:
                    elapsed = current_time - last_call_time
                    if elapsed < min_interval:
                        wait_time = min_interval - elapsed
                        await asyncio.sleep(wait_time)

                # Always update last_call_time to now, after any sleep
                last_call_time = time.monotonic()

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
