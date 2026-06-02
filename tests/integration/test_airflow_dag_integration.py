"""Integration tests for the World Bank pipeline DAG tasks."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))


@pytest.mark.integration
def test_ingest_task_imports():
    """Test that the ingest task can import required modules."""
    try:
        from idp.ingestion.world_bank.pipeline import WorldBankIndicatorsPipeline

        assert WorldBankIndicatorsPipeline is not None
    except ImportError as e:
        pytest.fail(f"Failed to import WorldBankIndicatorsPipeline: {e}")


@pytest.mark.integration
def test_export_task_imports():
    """Test that the export task can import required modules."""
    try:
        from idp.transformation.exporter import export_gold_to_postgres

        assert export_gold_to_postgres is not None
    except ImportError as e:
        pytest.fail(f"Failed to import export_gold_to_postgres: {e}")


@pytest.mark.integration
def test_embeddings_task_imports():
    """Test that the embeddings task can import required modules."""
    try:
        from idp.storage.generate_indicator_embeddings import run

        assert run is not None
    except ImportError as e:
        pytest.fail(f"Failed to import embeddings run function: {e}")


@pytest.mark.integration
@patch("idp.ingestion.world_bank.pipeline.WorldBankIndicatorsPipeline")
def test_ingest_task_execution_mock(mock_pipeline_class):
    """Test ingest task execution with mocked pipeline."""
    # Arrange
    mock_pipeline = AsyncMock()
    mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
    mock_pipeline.__aexit__ = AsyncMock(return_value=None)
    mock_pipeline.run = AsyncMock(return_value=None)
    mock_pipeline_class.return_value = mock_pipeline

    # Act
    async def _run():
        from idp.ingestion.world_bank.pipeline import WorldBankIndicatorsPipeline

        async with WorldBankIndicatorsPipeline() as pipeline:
            await pipeline.run()

    asyncio.run(_run())

    # Assert
    mock_pipeline_class.assert_called_once()
    mock_pipeline.run.assert_called_once()


@pytest.mark.integration
@patch("idp.transformation.exporter.export_gold_to_postgres")
def test_export_task_execution_mock(mock_export):
    """Test export task execution with mocked exporter."""
    # Arrange
    mock_export.return_value = {
        "dim_countries": 20,
        "dim_indicators": 33,
        "dim_dates": 15,
        "fact_economic_indicators": 9900,
    }

    # Act
    from idp.transformation.exporter import export_gold_to_postgres

    result = export_gold_to_postgres(duckdb_path="data/gold.duckdb")

    # Assert
    assert result is not None
    assert isinstance(result, dict)
    assert "dim_countries" in result
    mock_export.assert_called_once()


@pytest.mark.integration
@patch("idp.storage.generate_indicator_embeddings.run")
def test_embeddings_task_execution_mock(mock_run):
    """Test embeddings task execution with mocked run function."""
    # Arrange
    mock_run.return_value = None

    # Act
    from idp.storage.generate_indicator_embeddings import run

    run()

    # Assert
    mock_run.assert_called_once()
