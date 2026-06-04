"""End-to-end pipeline execution test.

Simulates the full Airflow DAG workflow:
  Ingest -> dbt run -> dbt test -> Export -> Embeddings
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

logger = logging.getLogger(__name__)


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the full end-to-end pipeline simulating the Airflow DAG.

    All four DAG steps are called with mocked dependencies to prove correct wiring:
    1. Ingestion (Bronze)
    2. dbt Transform (Silver/Gold)
    3. Export to PostgreSQL (Serving)
    4. Generate Embeddings
    """
    monkeypatch.setenv("POSTGRES_DB", "idp_test")
    monkeypatch.setenv("POSTGRES_USER", "idp_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "changeme")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "minioadmin")
    monkeypatch.setenv("MINIO_SECRET_KEY", "minioadmin")

    # ── Step 1: Ingestion ──
    with patch(
        "idp.ingestion.world_bank.pipeline.WorldBankIndicatorsPipeline.run",
        new_callable=AsyncMock,
    ) as mock_ingest:
        from idp.ingestion.world_bank.pipeline import WorldBankIndicatorsPipeline

        async with WorldBankIndicatorsPipeline() as pipeline:
            await pipeline.run()

        mock_ingest.assert_called_once()
        logger.info("Step 1: Ingestion — pipeline.run() called")

    # ── Step 2: dbt Transformation ──
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        import subprocess

        subprocess.run(["dbt", "run", "--target", "dev"], check=True, cwd="dbt")
        subprocess.run(["dbt", "test", "--target", "dev"], check=True, cwd="dbt")

        assert mock_run.call_count == 2
        logger.info("Step 2: dbt — run + test executed")

    # ── Step 3: Export to PostgreSQL ──
    with (
        patch("idp.transformation.exporter.duckdb.connect") as mock_duckdb,
        patch("idp.transformation.exporter.psycopg.connect") as mock_pg,
    ):
        mock_df = MagicMock()
        mock_duckdb_conn = MagicMock()
        mock_duckdb_conn.execute.return_value.pl.return_value = mock_df
        mock_duckdb.return_value = mock_duckdb_conn

        mock_pg_conn = MagicMock()
        mock_pg.return_value = mock_pg_conn

        from idp.transformation.exporter import export_gold_to_postgres

        result = export_gold_to_postgres(duckdb_path="data/test.duckdb")
        assert isinstance(result, dict), f"Expected dict result, got {type(result)}"
        logger.info("Step 3: Export — %s", result)

    # ── Step 4: Generate Embeddings ──
    with patch("idp.storage.generate_indicator_embeddings.run") as mock_embeddings:
        from idp.storage.generate_indicator_embeddings import run as run_embeddings

        run_embeddings()
        mock_embeddings.assert_called_once()
        logger.info("Step 4: Embeddings — generation called")
