"""Unit tests for Airflow callbacks."""

import os
import sys
from typing import Any
from unittest.mock import MagicMock

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../src"))

from idp.orchestration.callbacks import (
    dag_failure_alert,
    dag_success_alert,
    task_failure_alert,
)


@pytest.mark.unit
def test_task_failure_alert_logs_error(caplog: Any) -> None:
    """Test that task_failure_alert logs the error correctly."""
    # Arrange
    mock_task_instance = MagicMock()
    mock_task_instance.task_id = "test_task"
    mock_dag = MagicMock()
    mock_dag.dag_id = "test_dag"

    context: dict[str, Any] = {
        "task_instance": mock_task_instance,
        "dag": mock_dag,
        "execution_date": "2026-06-01",
        "exception": ValueError("Test error"),
    }

    # Act
    with caplog.at_level("ERROR"):
        task_failure_alert(context)

    # Assert
    assert "TASK FAILURE" in caplog.text
    assert "test_dag" in caplog.text
    assert "test_task" in caplog.text
    assert "Test error" in caplog.text


@pytest.mark.unit
def test_dag_failure_alert_logs_error(caplog: Any) -> None:
    """Test that dag_failure_alert logs the error correctly."""
    # Arrange
    mock_dag = MagicMock()
    mock_dag.dag_id = "test_dag"

    context: dict[str, Any] = {
        "dag": mock_dag,
        "execution_date": "2026-06-01",
    }

    # Act
    with caplog.at_level("ERROR"):
        dag_failure_alert(context)

    # Assert
    assert "DAG FAILURE" in caplog.text
    assert "test_dag" in caplog.text
    assert "2026-06-01" in caplog.text


@pytest.mark.unit
def test_dag_success_alert_logs_success(caplog: Any) -> None:
    """Test that dag_success_alert logs the success correctly."""
    # Arrange
    mock_dag = MagicMock()
    mock_dag.dag_id = "test_dag"

    context: dict[str, Any] = {
        "dag": mock_dag,
        "execution_date": "2026-06-01",
    }

    # Act
    with caplog.at_level("INFO"):
        dag_success_alert(context)

    # Assert
    assert "DAG SUCCESS" in caplog.text
    assert "test_dag" in caplog.text
    assert "2026-06-01" in caplog.text


@pytest.mark.unit
def test_task_failure_alert_handles_missing_context_keys() -> None:
    """Test that task_failure_alert gracefully handles missing context keys."""
    # Arrange - minimal context
    context: dict[str, Any] = {}

    # Act & Assert - should not raise exception
    try:
        task_failure_alert(context)
    except Exception as e:
        pytest.fail(f"task_failure_alert raised an exception with empty context: {e}")


@pytest.mark.unit
def test_callbacks_are_callable() -> None:
    """Test that all callback functions are callable."""
    assert callable(task_failure_alert)
    assert callable(dag_failure_alert)
    assert callable(dag_success_alert)
