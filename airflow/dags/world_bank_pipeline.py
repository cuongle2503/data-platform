import os
import sys
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

# Add src to path so we can import idp modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from idp.orchestration.callbacks import (
    dag_failure_alert,
    dag_success_alert,
    task_failure_alert,
)

default_args = {
    "owner": "data_platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=1),
    "on_failure_callback": task_failure_alert,
}


@dag(
    dag_id="world_bank_pipeline",
    default_args=default_args,
    schedule="@monthly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["world_bank", "idp"],
    on_success_callback=dag_success_alert,
    on_failure_callback=dag_failure_alert,
    doc_md=__doc__,
)
def world_bank_pipeline():
    """End-to-end pipeline for World Bank data: Ingestion -> Transform -> Serving -> Embeddings"""

    @task(retries=2)
    def ingest_bronze_data() -> None:
        """Run the World Bank data ingestion pipeline — fetches indicators
        from the World Bank API and saves to MinIO Bronze."""
        import asyncio
        import os
        import sys

        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

        from idp.ingestion.world_bank.pipeline import WorldBankIndicatorsPipeline

        async def _run() -> None:
            async with WorldBankIndicatorsPipeline() as pipeline:
                await pipeline.run()

        asyncio.run(_run())

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt/idp && HOME=/home/airflow /home/airflow/.local/bin/dbt run --target dev",
        env={"DBT_PROFILES_DIR": "/opt/airflow/dbt", "MINIO_ENDPOINT": "minio:9000"},
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt/idp && HOME=/home/airflow /home/airflow/.local/bin/dbt test --target dev",
        env={"DBT_PROFILES_DIR": "/opt/airflow/dbt", "MINIO_ENDPOINT": "minio:9000"},
    )

    @task(retries=2)
    def export_to_serving() -> dict[str, int]:
        """Export transformed data from DuckDB to PostgreSQL."""
        import os
        import sys

        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

        from idp.transformation.exporter import export_gold_to_postgres

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        duckdb_path = os.path.join(project_root, "data/gold.duckdb")

        return export_gold_to_postgres(duckdb_path=duckdb_path)

    @task(retries=2)
    def generate_embeddings() -> None:
        """Generate vector embeddings for imported indicators — stores
        results in PostgreSQL pgvector."""
        import os
        import sys

        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

        from idp.storage.generate_indicator_embeddings import run as run_embeddings

        run_embeddings()

    # ── Task Dependencies ──
    ingest = ingest_bronze_data()
    export = export_to_serving()
    embed = generate_embeddings()

    ingest >> dbt_run >> dbt_test >> export >> embed


world_bank_pipeline()
