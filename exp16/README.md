# Experiment 16: Nested Workflows with workflow_id Tracking

This experiment demonstrates a 3-level nested workflow hierarchy in DBOS, where each workflow and step prints its `workflow_id` to track execution flow and understand how workflow identities propagate through nested calls.

## Architecture

```
Top-Level Workflow (Entry Point)
    │
    └── Middle Workflow (Business Logic)
            │
            └── Leaf Workflow (Processing Work)
                    │
                    ├── Processing Step (Iteration 1)
                    ├── Processing Step (Iteration 2)
                    └── Processing Step (Iteration 3)
```

## File Structure

```
exp16/
├── main.py          # Complete nested workflow implementation
└── README.md        # This documentation
```

## Workflow Hierarchy

### 1. `top_level_workflow(project_name)` - Entry Point
- **Purpose**: Initiates the entire process and coordinates the overall flow
- **Logs**: workflow_id at start, when calling middle workflow, and at completion
- **Returns**: Final report with complete execution summary

### 2. `middle_workflow(task_name)` - Business Logic Layer
- **Purpose**: Orchestrates the main processing logic and manages business rules
- **Logs**: workflow_id at start, when calling leaf workflow, and at completion
- **Returns**: Summary with task details and processed results

### 3. `leaf_workflow(input_data)` - Processing Layer
- **Purpose**: Performs the actual work by calling DBOS steps iteratively
- **Logs**: workflow_id at start, during each iteration, and at completion
- **Calls**: `processing_step()` 3 times in a loop
- **Returns**: List of all step results

### 4. `processing_step(iteration, data)` - Atomic Work Unit
- **Purpose**: Performs individual processing tasks with simulation work
- **Type**: DBOS Step (not workflow)
- **Logs**: workflow_id at start and completion of each step
- **Work**: Simulates processing with 0.5s sleep
- **Returns**: Processed data string

## Key Features

### Workflow ID Tracking
Each workflow and step logs:
- Its own `DBOS.workflow_id`
- The workflow level (top/middle/leaf)
- Execution context and timing

### Iterative Step Execution
The leaf workflow demonstrates:
- Calling the same DBOS step multiple times
- Maintaining workflow_id consistency across iterations
- Accumulating results from repeated step calls

### Nested Workflow Communication
Shows how data flows:
- From top-level → middle workflow
- From middle → leaf workflow
- From leaf workflow → processing steps
- Results propagating back up the chain

## Running the Experiment

```bash
# Ensure DBOS database is available
export DBOS_DATABASE_URL="postgresql://username:password@localhost:5432/database"

# Run the nested workflows experiment
python exp16/main.py
```

## Expected Output

The experiment will log workflow_id at each level:

1. **Top-level workflow** starts with its unique workflow_id
2. **Middle workflow** gets called with a new workflow_id
3. **Leaf workflow** receives another new workflow_id
4. **Each processing step** shows the leaf workflow's workflow_id (steps inherit parent workflow ID)

## Learning Objectives

- Understand how workflow_id propagates in nested DBOS workflows
- See the difference between workflow and step execution contexts
- Observe how DBOS maintains workflow identity through multiple levels
- Learn patterns for building complex, hierarchical workflow systems

## Notes

- Each workflow level gets its own unique `workflow_id`
- Steps inherit the `workflow_id` from their parent workflow
- All logging includes workflow_id for complete traceability
- The experiment simulates realistic nested business process patterns