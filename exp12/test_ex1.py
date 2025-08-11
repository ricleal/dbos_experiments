import os
from importlib import reload
from unittest.mock import patch

import pytest
from dbos import DBOS, DBOSConfig
from dbos._error import DBOSMaxStepRetriesExceeded
from ex1 import my_workflow


@pytest.fixture(scope="session")
def dbos_config():
    """Set up DBOS configuration for testing."""
    config: DBOSConfig = {
        "name": "test-dbos-ex1",
        "database_url": os.getenv(
            "TESTING_DATABASE_URL",
            "postgresql://trustle:trustle@localhost:5432/test?sslmode=disable",
        ),
        "log_level": "DEBUG",
    }
    DBOS(config=config)
    DBOS.reset_system_database()
    DBOS.launch()
    yield
    DBOS.destroy()


@pytest.fixture()
def dbos_config_mock_step():
    """Fixture that mocks DBOS.step decorator and provides module reload functionality."""

    # Mock the DBOS.step decorator to return a simple function without retry logic
    def mock_step_decorator(retries_allowed=True, **kwargs):
        def decorator(func):
            # Return the original function without any DBOS retry logic
            return func

        return decorator

    def reload_module(module):
        """Helper function to reload a module with mocked DBOS.step"""
        return reload(module)

    with patch("dbos.DBOS.step", side_effect=mock_step_decorator):
        yield reload_module


def test_workflow_fails_with_max_retries_exceeded(dbos_config):
    """Test that my_workflow fails with DBOSMaxStepRetriesExceeded after 3 retries."""
    # Start the workflow
    handle = DBOS.start_workflow(my_workflow)

    # Verify handle exists
    assert handle is not None
    assert handle.workflow_id is not None

    # The workflow should fail with DBOSMaxStepRetriesExceeded
    with pytest.raises(
        DBOSMaxStepRetriesExceeded,
        match="Step failure_step has exceeded its maximum of 3 retries",
    ):
        handle.get_result()

    # Verify workflow status shows ERROR
    status = handle.get_status()
    assert status.status == "ERROR"
    assert status.name == "my_workflow"


def test_workflow_fails_fast_with_mocked_step(dbos_config):
    """Fast test that mocks DBOS.step to avoid retries and test only the exception."""

    # Mock the DBOS.step decorator to return a simple function without retry logic
    def mock_step_decorator(retries_allowed=True, **kwargs):
        def decorator(func):
            # Return the original function without any DBOS retry logic
            return func

        return decorator

    # Start the workflow
    handle = DBOS.start_workflow(my_workflow)

    # Verify handle exists
    assert handle is not None
    assert handle.workflow_id is not None

    with patch("dbos.DBOS.step", side_effect=mock_step_decorator):
        # Import the functions after mocking to get the mocked versions

        import ex1

        reload(ex1)

        # The workflow now fails with the exception thrown by failure_step
        with pytest.raises(
            ValueError,
            match="Simulated failure in failure_step",
        ):
            handle.get_result()

        # Verify workflow status shows ERROR
        status = handle.get_status()
        assert status.status == "ERROR"
        assert status.name == "my_workflow"


def test_steps_with_fixture_mock(dbos_config, dbos_config_mock_step):
    """New test using the dbos_config_mock_step fixture."""
    # Reload the ex1 module to apply the mocked DBOS.step decorator
    import ex1

    dbos_config_mock_step(ex1)
    # Start the workflow
    handle = DBOS.start_workflow(my_workflow)

    # Verify handle exists
    assert handle is not None
    assert handle.workflow_id is not None

    # The workflow now fails with the exception thrown by failure_step
    with pytest.raises(
        ValueError,
        match="Simulated failure in failure_step",
    ):
        handle.get_result()

    # Verify workflow status shows ERROR
    status = handle.get_status()
    assert status.status == "ERROR"
    assert status.name == "my_workflow"
