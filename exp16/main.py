import os
import time
from pprint import pprint

from dbos import DBOS, DBOSConfig

"""
Experiment 16: Nested Workflows with workflow_id Tracking

This experiment demonstrates 3 levels of nested workflows where:
1. Top-level workflow starts the process
2. Middle-level workflow orchestrates the main logic
3. Leaf workflow performs iterative work with DBOS steps

Each workflow and step prints its workflow_id to track the execution hierarchy.
"""

config: DBOSConfig = {
    "name": "nested-workflows-exp",
    "database_url": os.environ.get(
        "DBOS_DATABASE_URL",
        "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
    ),
    "log_level": "INFO",
}
DBOS(config=config)

# Global list to track all workflow IDs for status checking
workflow_ids = []


def track_workflow_id(workflow_level: str):
    """Track the current workflow ID for later status checking"""
    workflow_ids.append(
        {
            "workflow_id": DBOS.workflow_id,
            "level": workflow_level,
            "name": f"{workflow_level}_workflow",
        }
    )


def print_all_workflow_statuses():
    """Retrieve and print the status of all tracked workflows"""
    print("\n" + "=" * 80)
    print("WORKFLOW STATUS REPORT")
    print("=" * 80)

    for workflow_info in workflow_ids:
        workflow_id = workflow_info["workflow_id"]
        level = workflow_info["level"]
        name = workflow_info["name"]

        try:
            # Get the workflow status
            handle = DBOS.retrieve_workflow(workflow_id)
            status = handle.get_status()

            print(f"\n📋 {name.upper()} ({level} level)")
            print(f"   Workflow ID: {workflow_id}")
            print(f"   Status: {status.status}")
            print(f"   Name: {status.name}")
            print(f"   Created At: {status.created_at}")
            print(f"   Updated At: {status.updated_at}")
            print(f"   Recovery Attempts: {status.recovery_attempts}")

            if status.output is not None:
                print(f"   Has Output: Yes (type: {type(status.output).__name__})")
            else:
                print("   Has Output: No")

            if status.error is not None:
                print(f"   Error: {status.error}")
            else:
                print("   Error: None")

        except Exception as e:
            print(f"\n❌ {name.upper()} ({level} level)")
            print(f"   Workflow ID: {workflow_id}")
            print(f"   Error retrieving status: {e}")

    print("\n" + "=" * 80)


@DBOS.step()
def processing_step(iteration: int, data: str) -> str:
    """A DBOS step that simulates some processing work"""
    DBOS.logger.info(
        {
            "message": "Processing Step Executing",
            "workflow_id": DBOS.workflow_id,
            "iteration": iteration,
            "input_data": data,
            "step_type": "processing_step",
        }
    )

    # Simulate some work
    time.sleep(0.5)
    result = f"processed_{data}_iteration_{iteration}"

    DBOS.logger.info(
        {
            "message": "Processing Step Completed",
            "workflow_id": DBOS.workflow_id,
            "iteration": iteration,
            "result": result,
            "step_type": "processing_step",
        }
    )

    return result


@DBOS.workflow()
def leaf_workflow(input_data: str) -> list[str]:
    """
    Leaf workflow: Calls processing_step 3 times iteratively
    This is the innermost workflow that does the actual work
    """
    # Track this workflow for status reporting
    track_workflow_id("leaf")

    DBOS.logger.info(
        {
            "message": "Leaf Workflow Started",
            "workflow_id": DBOS.workflow_id,
            "input_data": input_data,
            "workflow_level": "leaf",
        }
    )

    results = []
    for i in range(1, 4):  # 3 iterations
        DBOS.logger.info(
            {
                "message": "Leaf Workflow Iteration",
                "workflow_id": DBOS.workflow_id,
                "iteration": i,
                "workflow_level": "leaf",
            }
        )

        # Call the DBOS step
        step_result = processing_step(i, input_data)
        results.append(step_result)

    DBOS.logger.info(
        {
            "message": "Leaf Workflow Completed",
            "workflow_id": DBOS.workflow_id,
            "results_count": len(results),
            "workflow_level": "leaf",
        }
    )

    return results


@DBOS.workflow()
def middle_workflow(task_name: str) -> dict:
    """
    Middle workflow: Orchestrates the main processing logic
    This workflow manages the business logic and calls the leaf workflow
    """
    # Track this workflow for status reporting
    track_workflow_id("middle")

    DBOS.logger.info(
        {
            "message": "Middle Workflow Started",
            "workflow_id": DBOS.workflow_id,
            "task_name": task_name,
            "workflow_level": "middle",
        }
    )

    # Prepare data for the leaf workflow
    input_data = f"task_{task_name}_data"

    DBOS.logger.info(
        {
            "message": "Middle Workflow Calling Leaf Workflow",
            "workflow_id": DBOS.workflow_id,
            "prepared_data": input_data,
            "workflow_level": "middle",
        }
    )

    # Call the leaf workflow
    leaf_results = leaf_workflow(input_data)

    # Process the results
    summary = {
        "task_name": task_name,
        "total_results": len(leaf_results),
        "results": leaf_results,
        "processed_by_workflow": DBOS.workflow_id,
    }

    DBOS.logger.info(
        {
            "message": "Middle Workflow Completed",
            "workflow_id": DBOS.workflow_id,
            "summary": summary,
            "workflow_level": "middle",
        }
    )

    return summary


@DBOS.workflow()
def top_level_workflow(project_name: str) -> dict:
    """
    Top-level workflow: Entry point that starts the entire process
    This workflow initiates the overall task and coordinates the flow
    """
    # Track this workflow for status reporting
    track_workflow_id("top")

    DBOS.logger.info(
        {
            "message": "Top-Level Workflow Started",
            "workflow_id": DBOS.workflow_id,
            "project_name": project_name,
            "workflow_level": "top",
        }
    )

    # Generate task name for middle workflow
    task_name = f"{project_name}_main_task"

    DBOS.logger.info(
        {
            "message": "Top-Level Workflow Calling Middle Workflow",
            "workflow_id": DBOS.workflow_id,
            "task_name": task_name,
            "workflow_level": "top",
        }
    )

    # Call the middle workflow
    middle_result = middle_workflow(task_name)

    # Create final report
    final_report = {
        "project_name": project_name,
        "initiated_by_workflow": DBOS.workflow_id,
        "middle_workflow_result": middle_result,
        "execution_summary": "3-level nested workflow execution completed",
    }

    DBOS.logger.info(
        {
            "message": "Top-Level Workflow Completed",
            "workflow_id": DBOS.workflow_id,
            "final_report": final_report,
            "workflow_level": "top",
        }
    )

    return final_report


if __name__ == "__main__":
    DBOS.launch()

    DBOS.logger.info(
        {
            "message": "Starting Nested Workflows Experiment",
            "experiment": "exp16",
            "description": "3-level nested workflows with workflow_id tracking",
        }
    )

    # Execute the top-level workflow
    result = top_level_workflow("NestedWorkflowDemo")

    print("\n" + "=" * 60)
    print("EXPERIMENT 16 - NESTED WORKFLOWS COMPLETED")
    print("=" * 60)
    pprint(result)
    print("=" * 60)

    # Print the status of all workflows
    print_all_workflow_statuses()
