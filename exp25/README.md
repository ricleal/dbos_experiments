# Experiment 25: Multiple Queues with Rate Limiters and Partitioning

## Overview

This example demonstrates how to use **DBOS queues with different rate limiters** to **control the rate of HTTP requests** to external APIs. The example simulates managing API requests to multiple cloud providers (AWS, Azure, GCP) for different data types (users, groups, permissions), where each data type has different rate limits imposed by the external API.

**Key Use Case**: Preventing API rate limit violations when calling third-party services that have different rate limits for different endpoints.

## Why This Matters

When building applications that call external APIs (GitHub, Stripe, AWS, etc.), you face several challenges:

❌ **Without Rate Limiting:**
- Your app makes HTTP requests as fast as possible
- External API returns 429 "Too Many Requests" errors
- Requests fail, users see errors, data doesn't sync
- May get temporarily or permanently banned from the API

✅ **With DBOS Queue Rate Limiting:**
- HTTP requests are automatically controlled at the source
- Never exceed external API limits
- No 429 errors, no failed requests, no bans
- Different endpoints can have different rate limits
- Handles concurrent requests from multiple workers/processes
- Automatic retry and durability built-in

**This example shows you how to build reliable API integrations that respect rate limits.**

## Key Concepts

### HTTP Request Rate Limiting

The core purpose of this example is to demonstrate how DBOS queues can enforce rate limits on outbound HTTP requests to external APIs. Each queue represents a different API endpoint with its own rate limit:

```python
# Simulates a fast API endpoint (e.g., simple user lookups)
queue_users = Queue("queue_users", partition_queue=True, concurrency=1, limiter={"limit": 2, "period": 1})
# → 2 HTTP requests per second

# Simulates a moderate API endpoint (e.g., group queries)
queue_groups = Queue("queue_groups", partition_queue=True, concurrency=1, limiter={"limit": 2, "period": 5})
# → 2 HTTP requests every 5 seconds (0.4 req/s)

# Simulates a slow/expensive API endpoint (e.g., permission checks)
queue_permissions = Queue("queue_permissions", partition_queue=True, concurrency=1, limiter={"limit": 3, "period": 10})
# → 3 HTTP requests every 10 seconds (0.3 req/s)
```

**How it works:**
1. Your application enqueues tasks to make HTTP requests
2. DBOS queues enforce the rate limits before executing the requests
3. HTTP requests are made only when the rate limit allows
4. External API stays within rate limits, avoiding 429 errors

### Queue Partitioning

Each queue is partitioned by **provider** (AWS, Azure, GCP). This ensures:
- **Requests for the same provider are processed in order** within each queue
- **Different providers can make HTTP requests concurrently** (within rate limits)
- **Rate limits apply globally per queue**, not per partition
- **Each provider gets fair access** to the rate-limited HTTP endpoints

Example: If AWS, Azure, and GCP each need to make user requests, they share the same `queue_users` rate limit (2 req/1s), but their requests are processed in separate partitions to maintain ordering per provider.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Application                         │
│                                                               │
│  Endpoints trigger workflows per provider                    │
│  (/provider/{provider}/data_type/{data_type}?n=5)           │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │AWS Workflow  │  │Azure Workflow│  │GCP Workflow  │      │
│  │(background)  │  │(background)  │  │(background)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         └──────────Enqueue to Rate-Limited Queues───────────┘│
│                            ▼                                  │
├─────────────────────────────────────────────────────────────┤
│              DBOS Queue System (Rate Limiters)               │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐│
│  │  queue_users     │  │  queue_groups    │  │queue_perms  ││
│  │  2 req / 1 sec   │  │  2 req / 5 sec   │  │3 req/10 sec ││
│  │  ⏱️ HTTP Rate    │  │  ⏱️ HTTP Rate    │  │⏱️ HTTP Rate ││
│  │    Limiter       │  │    Limiter       │  │   Limiter   ││
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬──────┘│
│           │                     │                     │       │
│   ┌───────┴─────┬───────────────┴─────┬───────────────┴────┐│
│   │ aws         │ azure               │ gcp                ││
│   │ partition   │ partition           │ partition          ││
│   └─────────────┴─────────────────────┴────────────────────┘│
│                            ▼                                  │
├─────────────────────────────────────────────────────────────┤
│           Rate-Limited HTTP Requests                         │
│           (to httpbin service)                               │
│                                                               │
│  GET http://localhost:8080/get  ← Controlled by rate limits │
└─────────────────────────────────────────────────────────────┘
```

**Flow:**
1. Endpoint receives request → Starts workflow for provider
2. Workflow enqueues N HTTP request tasks to appropriate queue
3. **Queue rate limiter controls when HTTP requests execute**
4. HTTP requests are made to httpbin at the controlled rate
5. Prevents overwhelming external API with too many requests

## Setup

### 1. Start Services

```bash
cd exp25
docker-compose up -d
```

This starts:
- **PostgreSQL** (port 5432) - DBOS system database
- **httpbin** (port 8080) - Test HTTP service

### 2. Run the Application

```bash
python main.py
```

The FastAPI server starts on `http://localhost:8000`

## Usage

### Test Specific Queue and Provider

```bash
# Enqueue 10 requests for AWS users
curl "http://localhost:8000/provider/aws/data_type/users?n=10"

# Enqueue 5 requests for Azure groups
curl "http://localhost:8000/provider/azure/data_type/groups?n=5"

# Enqueue 6 requests for GCP permissions
curl "http://localhost:8000/provider/gcp/data_type/permissions?n=6"
```

### Run Demo (All Combinations)

```bash
curl http://localhost:8000/demo
```

This starts **9 background workflows** (one per provider/data_type combination):
- AWS users, AWS groups, AWS permissions
- Azure users, Azure groups, Azure permissions
- GCP users, GCP groups, GCP permissions

Each workflow enqueues 5 HTTP request tasks to the appropriate rate-limited queue:
- **Total: 45 HTTP requests** will be made to httpbin
- **15 requests per provider** (5 users + 5 groups + 5 permissions)
- **15 requests per data type** (5 AWS + 5 Azure + 5 GCP)

**What to watch in the logs:**
- Users queue processes requests at ~2 req/second
- Groups queue processes requests at ~2 req/5 seconds  
- Permissions queue processes requests at ~3 req/10 seconds
- All HTTP requests are rate limited, preventing API overload

### View Information

```bash
# Get usage information
curl http://localhost:8000/
```

## What to Observe

### HTTP Request Rate Limiting in Action

Watch the logs to see how DBOS queues control the rate of HTTP requests. The logs show elapsed time from the first request for each provider/data_type combination:

```
[queue_users      ] [AWS  ][users      ] Request #1 -   0.00s
[queue_users      ] [AWS  ][users      ] Request #2 -   0.50s  ← ~0.5s gap (2 req/1s)
[queue_users      ] [AWS  ][users      ] Request #3 -   1.01s  ← ~0.5s gap
[queue_users      ] [AWS  ][users      ] Request #4 -   1.51s  ← ~0.5s gap
```

### Different HTTP Rate Limits per Queue

Each queue enforces its own rate limit on outbound HTTP requests:

- **queue_users** (2 req/1s): HTTP requests every ~0.5 seconds
- **queue_groups** (2 req/5s): HTTP requests in pairs, ~2.5 seconds apart
- **queue_permissions** (3 req/10s): HTTP requests in triplets, ~3.3 seconds apart

**Why this matters:** If you're calling external APIs (GitHub, AWS, Stripe, etc.), each API has different rate limits. Using multiple queues lets you respect each API's specific limits.

### Partition Behavior with HTTP Requests

Different providers can make HTTP requests concurrently (within rate limits):

```
[queue_users      ] [AWS  ][users      ] Request #1 -   0.00s
[queue_users      ] [AZURE][users      ] Request #1 -   0.01s  ← Different partition, concurrent
[queue_users      ] [GCP  ][users      ] Request #1 -   0.02s  ← Different partition, concurrent
[queue_users      ] [AWS  ][users      ] Request #2 -   0.51s  ← Same partition, rate limited
```

All three providers share the same HTTP rate limit (2 req/1s for users queue), but process concurrently in separate partitions.

## Key Learning Points

1. **🎯 HTTP Rate Limiting**: DBOS queues enforce rate limits on outbound HTTP requests to external APIs - preventing 429 errors
2. **🔀 Multiple Rate Limits**: Different queues for different API endpoints, each with appropriate limits matching the external API
3. **🔑 Partition Keys**: Using provider as partition key ensures ordered processing per provider while sharing rate limits
4. **⚡ Background Workflows**: Using `DBOS.start_workflow()` to launch workflows asynchronously
5. **🌐 Real HTTP Calls**: Every step makes actual HTTP requests to httpbin (`GET /get`)
6. **💪 DBOS Durability**: Workflows survive crashes and automatically resume - no duplicate or lost HTTP requests
7. **📊 Observable Rate Limiting**: Logs show elapsed time to verify rate limits are working correctly

**Real-World Use Cases:**
- **GitHub API**: 5000 requests/hour for authenticated users
- **Stripe API**: 100 req/second (test mode), 25 req/second (live mode)  
- **AWS APIs**: Varying limits per service and region
- **Any third-party API**: Respect rate limits to avoid throttling and bans

## Testing Scenarios

### Scenario 1: Single Provider, Single Data Type
```bash
curl "http://localhost:8000/provider/aws/data_type/users?n=5"
```
**Expected**: 5 HTTP requests processed at ~2 req/second (~0.5s between requests)
**What happens**: Workflow enqueues 5 tasks, queue rate limiter ensures they execute at controlled rate

### Scenario 2: Multiple Providers, Same Data Type
```bash
curl "http://localhost:8000/provider/aws/data_type/users?n=3"
curl "http://localhost:8000/provider/azure/data_type/users?n=3"  
curl "http://localhost:8000/provider/gcp/data_type/users?n=3"
```
**Expected**: 9 HTTP requests total, processed concurrently across partitions, sharing the 2 req/1s rate limit
**What happens**: All providers compete for the same rate limit, but maintain ordering within their partition

### Scenario 3: Same Provider, Different Data Types (Different Rate Limits)
```bash
curl "http://localhost:8000/provider/aws/data_type/users?n=4"
curl "http://localhost:8000/provider/aws/data_type/groups?n=4"
curl "http://localhost:8000/provider/aws/data_type/permissions?n=4"
```
**Expected**: 12 HTTP requests total across 3 different queues, each with different rate limits:
- Users: 4 requests at 2 req/1s (~0.5s gaps)
- Groups: 4 requests at 2 req/5s (~2.5s gaps)  
- Permissions: 4 requests at 3 req/10s (~3.3s gaps)

**What happens**: Demonstrates how different API endpoints can have different rate limits

## Cleanup

```bash
# Stop services
docker-compose down

# Clean up volumes (optional)
docker-compose down -v
```

## Code Structure

- **`main.py`**: Complete application with queues, workflows, and HTTP rate limiting
- **`docker-compose.yaml`**: PostgreSQL and httpbin services
- **Queue Definitions**: Three rate-limited queues controlling HTTP request rates
  - `queue_users`: 2 requests per 1 second
  - `queue_groups`: 2 requests per 5 seconds
  - `queue_permissions`: 3 requests per 10 seconds
- **Workflows**:
  - `aws_process_data_request`, `azure_process_data_request`, `gcp_process_data_request` - Provider-specific workflows
  - `generic_process_data_request` - Generic workflow that enqueues HTTP request tasks
- **Step**: `make_http_request` - Makes actual HTTP GET request to httpbin
- **Endpoints**: 
  - `/provider/{provider}/data_type/{data_type}?n=N` - Test specific combinations
  - `/demo` - Run full demonstration

## Implementation Details

### HTTP Rate Limiting Architecture

The application uses DBOS queues to control the rate of outbound HTTP requests:

1. **Workflow Phase**: 
   - Provider workflow runs in background (started with `DBOS.start_workflow()`)
   - Workflow enqueues N tasks to the appropriate queue based on data type
   - Each task will make one HTTP request

2. **Queue Rate Limiting Phase**:
   - Queue controls when tasks execute based on rate limiter configuration
   - Tasks execute only when rate limit allows
   - Multiple partitions can share the same rate limit

3. **HTTP Request Phase**:
   - `make_http_request` step executes
   - Makes actual HTTP GET request to `http://localhost:8080/get`
   - Returns status code
   
**Code Example:**
```python
# Define queue with HTTP rate limit
queue_users = Queue(
    "queue_users",
    partition_queue=True,
    concurrency=1,
    limiter={"limit": 2, "period": 1}  # 2 HTTP requests per second
)

# Enqueue HTTP request task with partition key
with SetEnqueueOptions(queue_partition_key="aws"):
    queue_users.enqueue(
        make_http_request,  # This will make the actual HTTP call
        provider="aws",
        data_type="users",
        request_num=1
    )
```

### Logging and Observability

The application tracks elapsed time for each provider/data_type combination to verify rate limiting:

```python
# Track start times per combination
_start_times: dict[tuple[Provider, DataType], float] = {}

# In make_http_request step
key = (provider, data_type)
if key not in _start_times:
    _start_times[key] = time.time()

elapsed_from_start = time.time() - _start_times[key]

logger.info(
    f"[{queue_name:18s}] [{provider.upper():5s}][{data_type:11s}] "
    f"Request #{request_num} - {elapsed_from_start:6.2f}s"
)
```

This produces logs like:
```
[queue_users      ] [AWS  ][users      ] Request #1 -   0.00s
[queue_users      ] [AWS  ][users      ] Request #2 -   0.51s  ← 0.5s gap shows rate limiting
[queue_users      ] [AWS  ][users      ] Request #3 -   1.02s  ← 0.5s gap shows rate limiting
```

### Running the Demo

```bash
# Start services
cd exp25
docker-compose up -d

# Run the application
python main.py

# In another terminal, trigger the demo
curl http://localhost:8000/demo

# Watch the logs to see HTTP rate limiting in action
# You'll see requests being controlled at:
# - 2 req/1s for users
# - 2 req/5s for groups  
# - 3 req/10s for permissions
```
