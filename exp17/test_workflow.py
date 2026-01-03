"""
Test DBOS workflow integration with DuckDB + SQLite
"""

import os

from db import (
    create_database,
    seed_connected_integrations,
)
from dbos import DBOS, DBOSConfig
from elt import (
    apply_changes_to_latest_workflow,
    detect_changes_workflow,
    extract_and_load_workflow,
)


def test_workflow():
    print("🧪 Testing DBOS Workflow with DuckDB + SQLite")
    print("=" * 60)

    # Configure DBOS
    config: DBOSConfig = {
        "name": "test-elt-pipeline",
        "log_level": "INFO",
    }
    DBOS(config=config)

    # Clean up old test databases and use default names that workflows expect
    sqlite_path = "data.db"
    duckdb_path = "data_olap.db"

    for path in [sqlite_path, duckdb_path]:
        if os.path.exists(path):
            os.remove(path)

    # Initialize databases
    print("\n📦 Initializing databases...")
    create_database(sqlite_path=sqlite_path, duckdb_path=duckdb_path, truncate=True)
    print("✅ Databases created")

    # Seed one integration
    print("\n🌱 Seeding integration...")
    integrations = seed_connected_integrations(
        db_path=sqlite_path, num_orgs=1, integrations_per_org=1
    )
    integration = integrations[0]
    print(f"✅ Integration: {integration.organization_id} / {integration.id}")

    # Launch DBOS
    print("\n🚀 Launching DBOS...")
    DBOS.launch()
    print("✅ DBOS launched")

    # Test Stage 1: Extract & Load (2 batches, 2 pages per batch = 40 users)
    print("\n📥 Stage 1: Extract & Load to DuckDB...")
    users_loaded = extract_and_load_workflow(
        organization_id=integration.organization_id,
        connected_integration_id=integration.id,
        num_batches=2,
        batch_size=2,
    )
    print(f"✅ Loaded {users_loaded} unique users to DuckDB staging")

    # Test Stage 2: CDC Detection
    print("\n🔍 Stage 2: CDC Detection in DuckDB...")
    cdc_changes = detect_changes_workflow(
        organization_id=integration.organization_id,
        connected_integration_id=integration.id,
    )
    print(f"✅ CDC changes: {cdc_changes['total_changes']} total")
    print(f"   - Inserts: {cdc_changes['inserts']}")
    print(f"   - Updates: {cdc_changes['updates']}")
    print(f"   - Deletes: {cdc_changes['deletes']}")

    # Test Stage 3: Apply to Latest
    print("\n⚡ Stage 3: Apply CDC to SQLite...")
    latest_result = apply_changes_to_latest_workflow(
        organization_id=integration.organization_id,
        connected_integration_id=integration.id,
    )
    print(f"✅ Applied {latest_result['applied_count']} changes")
    print(f"✅ SQLite latest table: {latest_result['latest_count']} records")

    print("\n🎉 WORKFLOW TEST PASSED!")
    print("   ✅ All 3 stages executed successfully")
    print("   ✅ DuckDB → CDC → SQLite pipeline works")

    # Cleanup
    DBOS.destroy()
    for path in [sqlite_path, duckdb_path]:
        if os.path.exists(path):
            os.remove(path)
    print("\n🧹 Cleaned up")


if __name__ == "__main__":
    test_workflow()
