"""
ELT Pipeline with DBOS Workflows

This module implements a complete ELT (Extract, Load, Transform) pipeline using DBOS workflows.
The pipeline processes users from multiple organizations and connected integrations.

Architecture:
- Root workflow: Orchestrates ELT pipelines for all org/integration pairs
- ELT workflow: Runs sequential sub-workflows for each pair
- Sub-workflows: Extract, CDC detection, apply changes, sync to main DB
"""

import random
from typing import List
from uuid import UUID

# Import data models and generation functions
from data import User, generate_fake_users

# Import database operations
from db import (
    get_all_connected_integrations,
    get_unique_user_count,
    insert_users_batch,
)
from dbos import DBOS, Queue

# ============================================================================
# DBOS Queue for External Triggering
# ============================================================================

# Queue for workflows that can be triggered remotely via DBOSClient
elt_queue = Queue("elt_queue", concurrency=5)

# ============================================================================
# DBOS Steps
# ============================================================================


@DBOS.step(retries_allowed=True, max_attempts=3)
def fetch_users_from_api(
    organization_id: str,
    connected_integration_id: UUID,
    page: int,
) -> List[User]:
    """Simulate fetching users from an external API.

    This step may fail intermittently to simulate API failures.

    Args:
        organization_id: The organization ID
        connected_integration_id: The connected integration ID
        page: Page number for pagination

    Returns:
        List of User objects
    """
    DBOS.logger.info(
        f"Step: Fetching users from API for org={organization_id}, "
        f"integration={connected_integration_id}, page={page} "
        f"(workflow_id={DBOS.workflow_id})"
    )

    user_list = generate_fake_users(
        organization_id=organization_id,
        connected_integration_id=connected_integration_id,
        seed=page + hash(str(connected_integration_id)) % 1000,
        size=10,
    )

    # Simulate API failure (2% chance)
    if random.random() < 0.02:
        raise Exception("Simulated API failure")

    # DBOS.logger.info(f"Step: Successfully fetched {len(user_list)} users from API")
    return user_list


@DBOS.step(
    retries_allowed=True, max_attempts=10, backoff_rate=0.1, interval_seconds=0.1
)
def insert_users_to_staging(
    user_list: List[User],
    workflow_id: str,
    db_path: str = "data.db",
) -> None:
    """Insert users into staging table with simulated random failures.

    This step may fail intermittently to simulate database insertion failures.
    Note: Failures occur AFTER insertion, so duplicates may be created on retry.

    Args:
        user_list: List of users to insert
        workflow_id: Workflow ID for tracking
        db_path: Path to database
    """
    DBOS.logger.info(
        f"Step: Inserting {len(user_list)} users to staging table "
        f"(workflow_id={DBOS.workflow_id})"
    )

    insert_users_batch(
        user_list=user_list,
        workflow_id=workflow_id,
        db_path=db_path,
    )

    # Simulate database insertion failure (40% chance)
    if random.random() < 0.4:
        raise Exception("Simulated database insertion failure")

    DBOS.logger.info("Step: Users inserted successfully to staging")


# ============================================================================
# Sub-Workflows
# ============================================================================


@DBOS.workflow(max_recovery_attempts=100)
def extract_and_load_batch_workflow(
    organization_id: str,
    connected_integration_id: UUID,
    batch_number: int,
    batch_size: int = 10,
) -> int:
    """Process a single batch of users (extract and load).

    This workflow fetches multiple pages of users and inserts them as a batch.

    Args:
        organization_id: The organization ID
        connected_integration_id: The connected integration ID
        batch_number: The batch number (1-indexed)
        batch_size: Number of pages per batch

    Returns:
        Count of users in this batch
    """
    DBOS.logger.info(
        f"Workflow [Extract & Load Batch {batch_number}]: Starting for org={organization_id}, "
        f"integration={connected_integration_id} "
        f"(workflow_id={DBOS.workflow_id})"
    )

    batch_users = []

    # Fetch multiple pages for this batch
    for page_in_batch in range(1, batch_size + 1):
        page = (batch_number - 1) * batch_size + page_in_batch

        DBOS.logger.info(
            f"Workflow [Extract & Load Batch {batch_number}]: Processing page {page_in_batch}/{batch_size}"
        )

        # Fetch users from API
        user_list = fetch_users_from_api(
            organization_id=organization_id,
            connected_integration_id=connected_integration_id,
            page=page,
        )

        batch_users.extend(user_list)

    # Insert the entire batch to staging table
    DBOS.logger.info(
        f"Workflow [Extract & Load Batch {batch_number}]: Inserting {len(batch_users)} users"
    )
    insert_users_to_staging(
        user_list=batch_users,
        workflow_id=DBOS.workflow_id[:36],
    )

    DBOS.logger.info(
        f"Workflow [Extract & Load Batch {batch_number}]: Completed. Processed {len(batch_users)} users"
    )
    return len(batch_users)


@DBOS.workflow(max_recovery_attempts=100)
def extract_and_load_workflow(
    organization_id: str,
    connected_integration_id: UUID,
    num_batches: int = 10,
    batch_size: int = 10,
) -> int:
    """Extract users from API and load into staging table (batch-based).

    This workflow processes users in batches, where each batch contains multiple
    pages of users. Each batch is processed by a sub-workflow.

    Args:
        organization_id: The organization ID
        connected_integration_id: The connected integration ID
        num_batches: Number of batches to process
        batch_size: Number of pages per batch

    Returns:
        Count of unique users loaded
    """
    DBOS.logger.info(
        f"Workflow [Extract & Load]: Starting for org={organization_id}, "
        f"integration={connected_integration_id}, "
        f"num_batches={num_batches}, batch_size={batch_size} "
        f"(workflow_id={DBOS.workflow_id})"
    )

    # Process each batch
    for batch_number in range(1, num_batches + 1):
        DBOS.logger.info(
            f"Workflow [Extract & Load]: Processing batch {batch_number}/{num_batches}"
        )

        # Process this batch using the batch workflow
        extract_and_load_batch_workflow(
            organization_id=organization_id,
            connected_integration_id=connected_integration_id,
            batch_number=batch_number,
            batch_size=batch_size,
        )

        # Simulate OOM error (5% chance after batch 5)
        if batch_number > 5 and random.random() < 0.05:
            import ctypes

            ctypes.string_at(0)

    # Get unique user count (handles duplicates from retries)
    user_count = get_unique_user_count(
        workflow_id=DBOS.workflow_id[:36],
        organization_id=organization_id,
        connected_integration_id=connected_integration_id,
    )

    DBOS.logger.info(
        f"Workflow [Extract & Load]: 🏹 Completed. Loaded {user_count} unique users"
    )
    return user_count


@DBOS.workflow()
def detect_changes_workflow(
    organization_id: str,
    connected_integration_id: UUID,
) -> str:
    """Detect changes and populate CDC table (mock workflow).

    This is a mock workflow that simulates CDC detection logic.

    Args:
        organization_id: The organization ID
        connected_integration_id: The connected integration ID

    Returns:
        Status message
    """
    DBOS.logger.info(
        f"Workflow [CDC Detection]: Starting for org={organization_id}, "
        f"integration={connected_integration_id} "
        f"(workflow_id={DBOS.workflow_id})"
    )

    # Simulate CDC detection processing
    DBOS.sleep(2)

    message = (
        f"CDC detection completed for org={organization_id}, "
        f"integration={connected_integration_id}"
    )

    DBOS.logger.info(f"Workflow [CDC Detection]: {message}")
    return message


@DBOS.workflow()
def apply_changes_to_latest_workflow(
    organization_id: str,
    connected_integration_id: UUID,
) -> int:
    """Apply changes to latest table using window function.

    This workflow uses a window function to get unique latest records
    from the staging table.

    Args:
        organization_id: The organization ID
        connected_integration_id: The connected integration ID

    Returns:
        Count of records in latest table
    """
    DBOS.logger.info(
        f"Workflow [Apply to Latest]: Starting for org={organization_id}, "
        f"integration={connected_integration_id} "
        f"(workflow_id={DBOS.workflow_id})"
    )

    # Get unique user count using window function
    unique_count = get_unique_user_count(
        organization_id=organization_id,
        connected_integration_id=connected_integration_id,
        workflow_id=DBOS.workflow_id[:36],
    )

    DBOS.logger.info(
        f"Workflow [Apply to Latest]: ▶️ Applied {unique_count} unique records to latest table"
    )

    return unique_count


@DBOS.workflow()
def sync_to_postgres_workflow(
    organization_id: str,
    connected_integration_id: UUID,
) -> str:
    """Sync changes to Postgres main database (mock workflow).

    This is a mock workflow that simulates syncing to a main database.

    Args:
        organization_id: The organization ID
        connected_integration_id: The connected integration ID

    Returns:
        Status message
    """
    DBOS.logger.info(
        f"Workflow [Sync to Postgres]: Starting for org={organization_id}, "
        f"integration={connected_integration_id} "
        f"(workflow_id={DBOS.workflow_id})"
    )

    # Simulate sync processing
    DBOS.sleep(1)

    message = (
        f"Synced to Postgres for org={organization_id}, "
        f"integration={connected_integration_id}"
    )

    DBOS.logger.info(f"Workflow [Sync to Postgres]: {message}")
    return message


# ============================================================================
# Main ELT Pipeline Workflow
# ============================================================================


@DBOS.workflow(max_recovery_attempts=100)
def elt_pipeline_workflow(
    organization_id: str,
    connected_integration_id: UUID,
) -> dict:
    """Run the complete ELT pipeline for a single org/integration pair.

    This workflow orchestrates all sub-workflows in sequence:
    1. Extract and Load
    2. Detect Changes (CDC)
    3. Apply to Latest Table
    4. Sync to Postgres

    Args:
        organization_id: The organization ID
        connected_integration_id: The connected integration ID

    Returns:
        Dictionary with results from each stage
    """
    DBOS.logger.info(
        f"🚀 Workflow [ELT Pipeline]: Starting for org={organization_id}, "
        f"integration={connected_integration_id} "
        f"(workflow_id={DBOS.workflow_id})"
    )

    # Stage 1: Extract and Load
    DBOS.logger.info("Workflow [ELT Pipeline]: Stage 1 - Extract & Load")
    users_loaded = extract_and_load_workflow(
        organization_id=organization_id,
        connected_integration_id=connected_integration_id,
    )

    # Stage 2: Detect Changes (CDC)
    DBOS.logger.info("Workflow [ELT Pipeline]: Stage 2 - CDC Detection")
    cdc_result = detect_changes_workflow(
        organization_id=organization_id,
        connected_integration_id=connected_integration_id,
    )

    # Stage 3: Apply to Latest Table
    DBOS.logger.info("Workflow [ELT Pipeline]: Stage 3 - Apply to Latest")
    latest_count = apply_changes_to_latest_workflow(
        organization_id=organization_id,
        connected_integration_id=connected_integration_id,
    )

    # Stage 4: Sync to Postgres
    DBOS.logger.info("Workflow [ELT Pipeline]: Stage 4 - Sync to Postgres")
    sync_result = sync_to_postgres_workflow(
        organization_id=organization_id,
        connected_integration_id=connected_integration_id,
    )

    result = {
        "organization_id": organization_id,
        "connected_integration_id": str(connected_integration_id),
        "users_loaded": users_loaded,
        "cdc_result": cdc_result,
        "latest_count": latest_count,
        "sync_result": sync_result,
    }

    DBOS.logger.info(
        f"✅ Workflow [ELT Pipeline]: Completed for org={organization_id}, "
        f"integration={connected_integration_id}"
    )

    return result


# ============================================================================
# Root Orchestration Workflow
# ============================================================================


@DBOS.workflow(max_recovery_attempts=50)
def root_orchestration_workflow() -> dict:
    """Root workflow that orchestrates ELT pipelines for all org/integration pairs.

    Fetches all connected integrations and triggers the ELT pipeline for each.

    Returns:
        Dictionary with results from all pipelines
    """
    DBOS.logger.info(
        f"🌟 Workflow [Root Orchestration]: Starting (workflow_id={DBOS.workflow_id})"
    )

    # Fetch all connected integrations
    integrations = get_all_connected_integrations()

    DBOS.logger.info(
        f"Workflow [Root Orchestration]: Found {len(integrations)} integrations to process"
    )

    results = []

    for idx, integration in enumerate(integrations, 1):
        DBOS.logger.info(
            f"Workflow [Root Orchestration]: Processing {idx}/{len(integrations)} - "
            f"org={integration.organization_id}, integration={integration.id}"
        )

        # Run ELT pipeline for this org/integration pair
        result = elt_pipeline_workflow(
            organization_id=integration.organization_id,
            connected_integration_id=integration.id,
        )

        results.append(result)

    summary = {
        "total_integrations": len(integrations),
        "results": results,
        "total_users": sum(r["users_loaded"] for r in results),
    }

    DBOS.logger.info(
        f"🎉 Workflow [Root Orchestration]: Completed. "
        f"Processed {len(integrations)} integrations, "
        f"loaded {summary['total_users']} total users"
    )

    return summary


# ============================================================================
# Scheduled Workflow
# ============================================================================


@DBOS.scheduled("20 5 * * *")  # Run daily at 5:20 AM GMT
@DBOS.workflow()
def scheduled_elt_trigger(scheduled_time, actual_time):
    """Scheduled workflow to trigger the root orchestration workflow.

    This workflow runs daily at 5:20 AM GMT and starts the root orchestration.

    Args:
        scheduled_time: When the workflow was scheduled to run
        actual_time: When the workflow actually started
    """
    DBOS.logger.info(
        f"⏰ Workflow [Scheduled Trigger]: Starting at {actual_time} "
        f"(scheduled for {scheduled_time})"
    )

    # Start the root orchestration workflow in the background
    handle = DBOS.start_workflow(root_orchestration_workflow)

    DBOS.logger.info(
        f"Workflow [Scheduled Trigger]: Started root orchestration "
        f"with workflow_id={handle.workflow_id}"
    )

    return handle.workflow_id
