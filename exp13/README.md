# Experiment 13: DBOS Workflow Examples with User Data Management

This folder contains three examples demonstrating different aspects of DBOS workflows for user data management and processing. All examples use a common data model and database setup to showcase various DBOS features including steps, workflows, error handling, and workflow recovery.

## Common Components

### Data Model (`data.py`)
- **`User` dataclass**: Represents a user with `id`, `external_id`, and `name`
- **`generate_fake_users()`**: Generates fake user data using Faker library
- **Unique ID generation**: Uses UUID5 to create deterministic UUIDs based on external_id and name

### Database Layer (`db.py`)
- **SQLite database** with a `users` table
- **Extended data model**: Adds `workflow_id`, `analyzed_at`, and `created_at` fields
- **Batch insertion**: Efficient insertion of user pages
- **Unique constraints**: Prevents duplicate entries based on `id`, `workflow_id`, and `analyzed_at`

## Example 1: Basic DBOS Workflow (`ex1.py`)

### Purpose
Demonstrates a simple, reliable DBOS workflow that processes user data in batches.

### Key Features
- **Basic workflow structure**: Simple step-based processing
- **Idempotent operations**: Can be run multiple times safely
- **Database truncation**: Starts with a clean database each run
- **Batch processing**: Processes users in pages of 10

### Workflow Flow
1. Create/truncate database
2. Generate and insert first batch of users (page 0)
3. Generate and insert second batch of users (page 1)
4. Return total user count

### Usage
```bash
python ex1.py
```

### Learning Points
- Basic DBOS workflow and step definitions
- Database integration with workflows
- Logging and monitoring workflow execution

---

## Example 2: Error Handling and Step Retries (`ex2.py`)

### Purpose
Demonstrates DBOS's automatic retry mechanism for handling transient errors in steps, while showing a **problematic pattern** that should be avoided.

### Key Features
- **Step retries**: `@DBOS.step(retries_allowed=True)` enables automatic retries
- **Simulated failures**: Artificially fails on early attempts to show retry behavior
- **Database constraints**: Uses unique constraints to prevent duplicate data insertion
- **Error simulation**: Throws `ValueError` on non-final attempts
- **⚠️ Step composition issue**: Demonstrates why steps should NOT combine data generation + database writing

### The Problem This Example Reveals
This example **doesn't work** by design to teach an important lesson:

```python
# ❌ PROBLEMATIC: Step combines generation + insertion
@DBOS.step(retries_allowed=True)
def users(page: int, workflow_id: str, analyzed_at: datetime) -> bool:
    user_list = get_fake_users(seed=page, size=10)  # Generate users
    insert_users_page(user_list, workflow_id, analyzed_at)  # Insert to DB
    # Simulate error after insert...
    raise ValueError("Simulated error")  # Step will be retried
```

**Why it fails**:
- **This doesn't work. A step is 2 operations: generate users and insert them into the DB**
- **I simulate an error after the insert, so the step can be retried**
- **However, on retry, the same users are generated and we try to insert them again**
- **Causing a UNIQUE constraint violation in the DB**

### Important Design Consideration
This example intentionally shows a **problematic pattern** where a single step combines:
1. Data generation (`get_fake_users()`)
2. Database insertion (`insert_users_page()`)

When the step fails after the database insertion and DBOS retries it, the retry will fail with:
```
sqlite3.IntegrityError: UNIQUE constraint failed: users.id, users.workflow_id, users.analyzed_at
```

**Best Practice**: Steps should be atomic and idempotent. For database operations, either:
- Use separate steps for data generation and insertion
- Design database operations to be truly idempotent (e.g., using `INSERT OR REPLACE`)
- Handle unique constraint violations gracefully within the step

### Workflow Flow
1. Create/truncate database
2. For each page (0, 1):
   - Generate users
   - Insert into database
   - Simulate error (except on final retry attempt)
   - DBOS automatically retries on failure
3. Return total user count

### Error Handling Logic
```python
# Fails on all attempts except the last one
if DBOS.step_status.current_attempt < DBOS.step_status.max_attempts - 1:
    raise ValueError(f"Simulated error on attempt {DBOS.step_status.current_attempt}")
```

### Usage
```bash
python ex2.py
```

### Learning Points
- Step-level error handling and retries
- Accessing step status information
- Designing idempotent operations for retry scenarios
- **⚠️ Critical lesson**: Why combining data generation + database writing in a single step is problematic
- Understanding unique constraint violations during retries

---

## Example 3: Workflow Recovery and Management (`ex3.py`)

### Purpose
Demonstrates DBOS's workflow recovery capabilities and workflow management features when facing catastrophic failures.

### Key Features
- **Workflow recovery**: `max_recovery_attempts=3` allows workflow to recover from crashes
- **Simulated crashes**: Uses `ctypes.string_at(0)` to simulate out-of-memory errors
- **Workflow detection**: Checks for existing pending workflows before starting new ones
- **Smart restart logic**: Waits for pending workflows and decides whether to resume or start fresh

### Workflow Flow
1. Check for existing pending workflows
2. If pending workflows exist:
   - Wait 5 seconds for potential completion
   - Resume existing workflow or start new one based on status
3. If no pending workflows: start new workflow
4. Execute workflow:
   - Create/truncate database
   - Insert first batch of users
   - **Simulate random crash** (50% chance)
   - Insert second batch of users (after recovery)
   - Return total user count

### Crash Simulation
```python
# 50% chance of simulating an out-of-memory error
if random.random() < 0.5:
    import ctypes
    ctypes.string_at(0)  # Causes segmentation fault
```

### Workflow Management Logic
```python
# Check for pending workflows
pending_workflows = DBOS.list_workflows(status=["PENDING", "ENQUEUED"], name="users_workflow")

if pending_workflows:
    # Wait and check again
    time.sleep(5)
    # Resume existing or start new based on updated status
```

### Usage
```bash
python ex3.py
```

### Learning Points
- Workflow recovery from catastrophic failures
- Workflow status management and querying
- Intelligent workflow restart logic
- Handling process crashes and restarts

---

## Example 4: Proper Step Design for Database Operations (`ex4.py`)

### Purpose
Demonstrates the **correct approach** for designing steps that work with database operations, avoiding the issues shown in Example 2.

### Key Features
- **Separated concerns**: Steps only generate data, workflows handle database operations
- **Proper retry handling**: No unique constraint violations during workflow retries
- **Crash recovery**: Similar to ex3 but with better step design
- **✅ Best practice implementation**: Shows how to properly structure steps and workflows

### Critical Design Decision
This example implements the **recommended pattern** where:

```python
# ✅ CORRECT: Step only generates data
@DBOS.step(retries_allowed=True)
def users(page: int) -> List[User]:
    user_list: List[User] = get_fake_users(seed=page, size=10)
    return user_list

# ✅ CORRECT: Workflow handles database operations
@DBOS.workflow(max_recovery_attempts=3)
def users_workflow() -> int:
    user_list = users(page=1)  # Step: generate data
    insert_users_page(user_list, DBOS.workflow_id, analyzed_at)  # Workflow: write to DB
```

### Why This Approach Works
- **The workflow step only generates users, and the insertion is done in the workflow**
- **The analyzed_at date is different for each retry of the workflow, although the workflow_id is the same**
- **This means that the combination of (user.id, workflow_id, analyzed_at) is always unique**
- **So no UNIQUE constraint violations will occur**

### Workflow Flow
1. Check for existing pending workflows (same smart logic as ex3)
2. Generate first batch of users (step)
3. Insert users to database (workflow)
4. **Simulate random crash** (50% chance)
5. Generate second batch of users (step)
6. Insert users to database (workflow)
7. Return total user count

### Comparison with Example 2
| Aspect | Example 2 (❌ Problematic) | Example 4 (✅ Correct) |
|--------|---------------------------|------------------------|
| Step responsibility | Generate + Insert data | Generate data only |
| Database operations | In step | In workflow |
| Retry behavior | Fails with constraint violation | Works correctly |
| Data uniqueness | Same analyzed_at on retry | New analyzed_at on retry |

### Usage
```bash
python ex4.py
```

### Learning Points
- **✅ Proper separation of concerns** between steps and workflows
- How workflow-level operations handle retries differently than step-level operations
- Why database writes should typically be done in workflows, not steps
- Understanding how DBOS handles workflow vs step recovery

---

## Running the Examples

### Prerequisites
1. **PostgreSQL database** running on `localhost:5432`
2. **Database**: `test` with user `trustle:trustle`
3. **Python dependencies**: Install using `pip install dbos faker`

### Environment Variables
Set the database URL (optional):
```bash
export DBOS_DATABASE_URL="postgresql://trustle:trustle@localhost:5432/test?sslmode=disable"
```

### Execution Order
1. Start with `ex1.py` to understand basic concepts
2. Run `ex2.py` to see error handling and retries (⚠️ problematic pattern)
3. Run `ex4.py` to see the correct approach for step design
4. Run `ex3.py` multiple times to observe crash recovery behavior

## Key DBOS Concepts Demonstrated

### Workflows
- Durable execution that survives process crashes
- Automatic recovery from the last completed step
- Workflow status tracking and management

### Steps
- Atomic operations within workflows
- Automatic retry mechanisms for transient failures
- Idempotent design patterns

### Error Handling
- Step-level retries with exponential backoff
- Workflow-level recovery attempts
- Graceful handling of various failure scenarios

### Database Integration
- Transaction management within steps
- Data consistency across workflow executions
- Unique constraints for preventing duplicates

This experiment series provides a comprehensive introduction to building resilient, distributed applications with DBOS.
