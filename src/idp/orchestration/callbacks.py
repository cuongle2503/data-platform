"""Airflow callback functions for monitoring and alerting."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def task_failure_alert(context: dict[str, Any]) -> None:
    """
    Callback function triggered when a task fails.

    This function logs the failure and can be extended to send alerts
    via email, Slack, PagerDuty, etc.

    Args:
        context: Airflow context dict containing task instance, DAG run info, etc.
    """
    task_instance = context.get("task_instance")
    task_id = task_instance.task_id if task_instance else "unknown_task"
    dag = context.get("dag")
    dag_id = dag.dag_id if dag else "unknown_dag"
    execution_date = context.get("execution_date")
    exception = context.get("exception")

    error_msg = (
        f"[TASK FAILURE] DAG: {dag_id} | Task: {task_id} | "
        f"Execution Date: {execution_date} | Exception: {exception}"
    )

    logger.error(error_msg)

    # TODO: Extend with email/Slack/PagerDuty integration
    # Example integrations:
    # - send_slack_alert(error_msg, channel="#data-alerts")
    # - send_email(subject=f"Task Failed: {task_id}", body=error_msg)
    # - trigger_pagerduty_incident(error_msg)


def dag_failure_alert(context: dict[str, Any]) -> None:
    """
    Callback function triggered when the entire DAG fails.

    Args:
        context: Airflow context dict containing DAG run info.
    """
    dag = context.get("dag")
    dag_id = dag.dag_id if dag else "unknown_dag"
    execution_date = context.get("execution_date")

    error_msg = f"[DAG FAILURE] DAG: {dag_id} | Execution Date: {execution_date}"

    logger.error(error_msg)

    # TODO: Extend with critical alerting channels
    # For DAG-level failures, consider using higher-priority channels


def dag_success_alert(context: dict[str, Any]) -> None:
    """
    Callback function triggered when the entire DAG succeeds.

    Useful for confirming successful pipeline runs, especially for critical
    daily/weekly/monthly pipelines.

    Args:
        context: Airflow context dict containing DAG run info.
    """
    dag = context.get("dag")
    dag_id = dag.dag_id if dag else "unknown_dag"
    execution_date = context.get("execution_date")

    success_msg = f"[DAG SUCCESS] DAG: {dag_id} | Execution Date: {execution_date}"

    logger.info(success_msg)

    # TODO: Optional success notifications
    # - send_slack_alert(success_msg, channel="#data-success")
