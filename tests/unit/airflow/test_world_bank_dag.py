"""Unit tests for the World Bank pipeline DAG."""

import os
import sys
from datetime import timedelta

import pytest

# Add airflow/dags to path so we can import the DAG module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../airflow/dags"))


def get_dag():
    """Import and return the DAG instance."""
    from world_bank_pipeline import world_bank_pipeline

    return world_bank_pipeline()


def test_dag_loads_without_errors():
    """Test that the DAG file can be imported without errors."""
    dag = get_dag()
    assert dag is not None
    assert dag.dag_id == "world_bank_pipeline"


def test_dag_structure():
    """Test the DAG has correct structure and configuration."""
    dag = get_dag()

    # In Airflow 3, it's 'schedule' rather than 'schedule_interval'
    assert dag.schedule == "@monthly"
    assert dag.catchup is False
    assert dag.max_active_runs == 1
    assert "world_bank" in dag.tags
    assert "idp" in dag.tags


def test_dag_has_correct_tasks():
    """Test that all required tasks are present in the DAG."""
    dag = get_dag()

    expected_tasks = {
        "ingest_bronze_data",
        "dbt_run",
        "dbt_test",
        "export_to_serving",
        "generate_embeddings",
    }

    actual_tasks = set(dag.task_ids)
    assert expected_tasks == actual_tasks, f"Expected {expected_tasks}, got {actual_tasks}"


def test_dag_task_dependencies():
    """Test that task dependencies are correctly defined."""
    dag = get_dag()

    # Get tasks
    ingest = dag.get_task("ingest_bronze_data")
    dbt_run = dag.get_task("dbt_run")
    dbt_test = dag.get_task("dbt_test")
    export = dag.get_task("export_to_serving")
    embeddings = dag.get_task("generate_embeddings")

    # Check dependencies: ingest -> dbt_run -> dbt_test -> export -> embeddings
    assert dbt_run in ingest.downstream_list
    assert dbt_test in dbt_run.downstream_list
    assert export in dbt_test.downstream_list
    assert embeddings in export.downstream_list


def test_dag_default_args():
    """Test that default_args are correctly configured."""
    dag = get_dag()

    assert dag.default_args["owner"] == "data_platform"
    assert dag.default_args["depends_on_past"] is False
    assert dag.default_args["retries"] == 2
    assert dag.default_args["retry_delay"] == timedelta(minutes=5)
    assert dag.default_args["execution_timeout"] == timedelta(hours=1)


@pytest.mark.parametrize(
    "task_id",
    [
        "ingest_bronze_data",
        "export_to_serving",
        "generate_embeddings",
    ],
)
def test_python_tasks_have_callables(task_id):
    """Test that Python tasks have valid callables."""
    dag = get_dag()
    task = dag.get_task(task_id)

    # For TaskFlow API tasks, check they have python_callable
    assert hasattr(task, "python_callable")
    assert task.python_callable is not None


@pytest.mark.parametrize("task_id", ["dbt_run", "dbt_test"])
def test_bash_tasks_have_commands(task_id):
    """Test that Bash tasks have valid commands."""
    dag = get_dag()
    task = dag.get_task(task_id)

    assert hasattr(task, "bash_command")
    assert "dbt" in task.bash_command
    assert task.bash_command is not None
    assert len(task.bash_command) > 0


def test_dag_idempotency_configuration():
    """Test that the DAG is configured for idempotent execution."""
    dag = get_dag()

    # Verify catchup is False (prevents backfilling)
    assert dag.catchup is False, "DAG must have catchup=False for idempotency"

    # Verify max_active_runs is 1 (prevents concurrent runs)
    assert dag.max_active_runs == 1, "DAG must have max_active_runs=1 for idempotency"

    # Verify retries are configured
    assert dag.default_args["retries"] >= 2, "DAG must have retries configured"


def test_dag_task_timeout_configured():
    """Test that tasks have execution timeout configured."""
    dag = get_dag()

    # Check that execution_timeout is set in default_args
    assert "execution_timeout" in dag.default_args
    assert dag.default_args["execution_timeout"] is not None
    assert dag.default_args["execution_timeout"] == timedelta(hours=1)
