"""
ELT Pipeline Client

This client can trigger DBOS workflows on demand by name with arbitrary parameters.
It connects to the ELT pipeline server and enqueues workflows remotely on the 'elt_queue'.

Usage examples:
    # Trigger the root orchestration workflow
    python client.py start root_orchestration_workflow

    # Trigger ELT pipeline for a specific org/integration
    python client.py start elt_pipeline_workflow \
        organization_id=org-001 \
        connected_integration_id=<uuid>

    # Trigger extract and load with custom parameters
    python client.py start extract_and_load_workflow \
        organization_id=org-001 \
        connected_integration_id=<uuid> \
        num_batches=5 \
        batch_size=20

    # Check workflow status
    python client.py status <workflow-id>

    # List workflows
    python client.py list
    python client.py list status=PENDING
    python client.py list status=SUCCESS limit=10

Note: All workflows are enqueued on the 'elt_queue' queue.
"""

import argparse
import asyncio
import json
import os
from uuid import UUID

from dbos import DBOSClient, EnqueueOptions, WorkflowHandleAsync

# Default queue name for ELT workflows
DEFAULT_QUEUE_NAME = "elt_queue"


def parse_parameter(param_str: str) -> tuple[str, any]:
    """Parse a parameter string in the format key=value.

    Automatically converts types:
    - Integers: "123" -> 123
    - Floats: "1.5" -> 1.5
    - Booleans: "true"/"false" -> True/False
    - JSON: "{...}" or "[...]" -> dict/list
    - UUIDs: strings matching UUID pattern -> UUID
    - Strings: everything else

    Args:
        param_str: Parameter string in format "key=value"

    Returns:
        Tuple of (key, converted_value)
    """
    if "=" not in param_str:
        raise ValueError(f"Invalid parameter format: {param_str}. Expected key=value")

    key, value = param_str.split("=", 1)
    key = key.strip()
    value = value.strip()

    # Try to convert value to appropriate type
    # 1. Boolean
    if value.lower() in ("true", "false"):
        return key, value.lower() == "true"

    # 2. JSON (dict or list)
    if (value.startswith("{") and value.endswith("}")) or (
        value.startswith("[") and value.endswith("]")
    ):
        try:
            return key, json.loads(value)
        except json.JSONDecodeError:
            pass

    # 3. Integer
    try:
        return key, int(value)
    except ValueError:
        pass

    # 4. Float
    try:
        return key, float(value)
    except ValueError:
        pass

    # 5. UUID (check if it looks like a UUID)
    if len(value) == 36 and value.count("-") == 4:
        try:
            return key, UUID(value)
        except ValueError:
            pass

    # 6. String (default)
    return key, value


async def trigger_workflow(workflow_name: str, params: list[str]) -> tuple[str, any]:
    """Trigger a workflow by name with arbitrary parameters.

    Args:
        workflow_name: Name of the workflow function to trigger
        params: List of parameter strings in format "key=value"

    Returns:
        Tuple of (workflow_id, result)
    """
    database_url = os.getenv(
        "DBOS_DATABASE_URL",
        "postgresql://postgres:dbos@localhost:5432/test?connect_timeout=10",
    )

    client = DBOSClient(database_url=database_url)

    print(f"Triggering workflow: {workflow_name}")

    # Parse parameters
    workflow_kwargs = {}
    for param in params:
        key, value = parse_parameter(param)
        workflow_kwargs[key] = value

    if workflow_kwargs:
        print(
            f"Parameters: {json.dumps({k: str(v) for k, v in workflow_kwargs.items()}, indent=2)}"
        )
    else:
        print("No parameters provided")

    # Create enqueue options with the queue name
    options: EnqueueOptions = {
        "queue_name": DEFAULT_QUEUE_NAME,
        "workflow_name": workflow_name,
    }

    # Enqueue the workflow
    handle: WorkflowHandleAsync = await client.enqueue_async(options, **workflow_kwargs)

    print(f"\n✅ Workflow enqueued with ID: {handle.workflow_id}")
    print("Waiting for workflow to complete...")

    # Wait for the workflow to complete and get the result
    result = await handle.get_result()

    print(f"\n{'=' * 60}")
    print("🎉 Workflow completed successfully!")
    print(f"{'=' * 60}")
    print(f"Workflow ID: {handle.workflow_id}")
    print(f"Result: {result}")
    print(f"{'=' * 60}\n")

    return handle.workflow_id, result


async def check_workflow_status(workflow_id: str):
    """Check the status of a running workflow.

    Args:
        workflow_id: The workflow ID to check
    """
    database_url = os.getenv(
        "DBOS_DATABASE_URL",
        "postgresql://postgres:dbos@localhost:5432/test?connect_timeout=10",
    )

    client = DBOSClient(database_url=database_url)

    print(f"Checking status of workflow: {workflow_id}")

    # Retrieve the workflow handle
    handle = await client.retrieve_workflow_async(workflow_id)

    # Get the status
    status = await handle.get_status()

    print(f"\n{'=' * 60}")
    print("Workflow Status")
    print(f"{'=' * 60}")
    print(f"Workflow ID: {workflow_id}")
    print(f"Status: {status.status}")
    print(f"Name: {status.name}")
    print(f"Created At: {status.created_at}")
    print(f"Updated At: {status.updated_at}")

    if status.status == "SUCCESS":
        print(f"Output: {status.output}")
    elif status.status == "ERROR":
        print(f"Error: {status.error}")

    print(f"{'=' * 60}\n")

    return status


async def list_workflows(params: list[str]):
    """List all workflows, optionally filtered by parameters.

    Args:
        params: List of parameter strings like "status=PENDING", "limit=10"
    """
    database_url = os.getenv(
        "DBOS_DATABASE_URL",
        "postgresql://postgres:dbos@localhost:5432/test?connect_timeout=10",
    )

    client = DBOSClient(database_url=database_url)

    # Parse parameters
    kwargs = {}
    for param in params:
        key, value = parse_parameter(param)
        kwargs[key] = value

    status_msg = "Listing workflows"
    if kwargs:
        status_msg += (
            f" with filters: {json.dumps({k: str(v) for k, v in kwargs.items()})}"
        )
    print(status_msg)

    # List workflows
    workflows = await client.list_workflows_async(**kwargs)

    print(f"\n{'=' * 60}")
    print(f"Found {len(workflows)} workflows")
    print(f"{'=' * 60}")

    for wf in workflows:
        print(f"\nWorkflow ID: {wf.workflow_id}")
        print(f"  Name: {wf.name}")
        print(f"  Status: {wf.status}")
        print(f"  Created: {wf.created_at}")
        print(f"  Updated: {wf.updated_at}")

    print(f"{'=' * 60}\n")

    return workflows


def main():
    """Main entry point for the client"""
    parser = argparse.ArgumentParser(
        description="ELT Pipeline Client - Trigger workflows on demand with generic parameters",
        epilog="""
Examples:
  # Start root orchestration
  %(prog)s start root_orchestration_workflow

  # Start ELT pipeline with parameters
  %(prog)s start elt_pipeline_workflow organization_id=org-001 connected_integration_id=<uuid>

  # Start with multiple parameters
  %(prog)s start extract_and_load_workflow organization_id=org-001 connected_integration_id=<uuid> num_batches=5 batch_size=20

  # Check status
  %(prog)s status <workflow-id>

  # List workflows with filters
  %(prog)s list
  %(prog)s list status=PENDING
  %(prog)s list status=SUCCESS limit=10
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Start workflow command
    start_parser = subparsers.add_parser(
        "start",
        help="Start a workflow with arbitrary parameters",
        description="Start a workflow by name with key=value parameters",
    )
    start_parser.add_argument(
        "workflow_name",
        help="Name of the workflow to trigger",
    )
    start_parser.add_argument(
        "params",
        nargs="*",
        help="Workflow parameters in format key=value (e.g., organization_id=org-001 num_batches=10)",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Check workflow status")
    status_parser.add_argument(
        "workflow_id",
        help="Workflow ID to check",
    )

    # List command
    list_parser = subparsers.add_parser(
        "list", help="List workflows with optional filters"
    )
    list_parser.add_argument(
        "params",
        nargs="*",
        help="Filter parameters in format key=value (e.g., status=PENDING limit=10)",
    )

    args = parser.parse_args()

    if args.command == "start":
        asyncio.run(
            trigger_workflow(
                workflow_name=args.workflow_name,
                params=args.params,
            )
        )
    elif args.command == "status":
        asyncio.run(check_workflow_status(args.workflow_id))
    elif args.command == "list":
        asyncio.run(list_workflows(params=args.params))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
