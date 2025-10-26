# Async Rate Limiter

A reusable async rate limiter decorator that evenly spaces function calls over time.

## Features

- **Even Spacing**: Distributes calls uniformly (not bursts)
- **Async-First**: Built with `asyncio`
- **Thread-Safe**: Uses `asyncio.Lock`
- **Zero Dependencies**: Python stdlib only
- **Type Hints**: Fully typed

## Installation

Copy `rate_limiter.py` to your project. No external dependencies!

## Usage

### Basic Example

```python
from rate_limiter import rate_limit

@rate_limit(calls=2, period=1)  # 2 calls/sec = 0.5s spacing
async def fetch_user(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        return response.json()
```

### With DBOS

```python
from dbos import DBOS
from rate_limiter import rate_limit

@rate_limit(calls=2, period=1)
@DBOS.step(retries_allowed=True)
async def call_api_step():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

### Common Patterns

```python
@rate_limit(calls=60, period=60)    # 1 per second
@rate_limit(calls=100, period=3600) # 100 per hour
@rate_limit(calls=10, period=1)     # 10 per second
```

## How It Works

1. Calculates `min_interval = period / calls`
2. Tracks last call time with `time.monotonic()`
3. Sleeps if next call is too soon
4. Uses `asyncio.Lock` for thread-safety

With `@rate_limit(calls=2, period=1)`:
- Call 1: 0.0s
- Call 2: 0.5s (after 0.5s wait)
- Call 3: 1.0s (after 0.5s wait)

## Testing

```bash
python rate_limiter.py              # Run example
poetry run pytest test_rate_limiter.py -v  # Run tests
```

## Why Even Spacing?

**Without even spacing** (bursts):
```
Time: 0.0s  0.01s  1.0s  1.01s
Call: 1     2      3     4
      ^^           ^^    Bursts!
```

**With even spacing**:
```
Time: 0.0s  0.5s  1.0s  1.5s
Call: 1     2     3     4
      ^     ^     ^     ^   Smooth!
```

Benefits: Reduces API load spikes, better compliance, avoids anti-abuse triggers.

## License

Free to use in any project!
