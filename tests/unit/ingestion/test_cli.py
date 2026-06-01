"""Unit tests for the CLI module."""

import argparse
from unittest.mock import AsyncMock, Mock, patch

import pytest

from idp.ingestion.cli import create_parser, main


def test_create_parser():
    """Test parser creation and arguments."""
    # Act
    parser = create_parser()

    # Assert
    assert isinstance(parser, argparse.ArgumentParser)

    # Test parse standard args
    args = parser.parse_args(
        ["ingest-indicators", "--countries", "VN,CN", "--start-year", "2020"]
    )
    assert args.command == "ingest-indicators"
    assert args.countries == "VN,CN"
    assert args.start_year == 2020
    assert args.end_year is None


@pytest.mark.asyncio
async def test_main_ingest_indicators():
    """Test main function with ingest-indicators command."""
    # Arrange
    with patch("idp.ingestion.cli.create_parser") as mock_create_parser:
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "ingest-indicators"
        mock_args.countries = "VN"
        mock_args.indicators = "NY.GDP.MKTP.CD"
        mock_args.start_year = 2023
        mock_args.end_year = 2023
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser

        with patch("idp.ingestion.cli.WorldBankIndicatorsPipeline") as mock_pipeline_cls:
            mock_pipeline_inst = AsyncMock()
            mock_pipeline_inst.run.return_value = [{"country_code": "VN", "value": 100}]
            mock_pipeline_cls.return_value = mock_pipeline_inst
            mock_pipeline_cls.return_value.__aenter__.return_value = mock_pipeline_inst

            with patch("idp.ingestion.cli.MinioClient") as mock_minio_cls:
                mock_minio = Mock()
                mock_minio.upload_dataframe.return_value = "bronze/test.parquet"
                mock_minio_cls.return_value = mock_minio

                # Act
                # We need to wrap main if it's not async, or just run it if it handles its own loop
                # Let's assume main() is async
                result = await main(["ingest-indicators", "--countries", "VN"])

    # Assert
    assert result == 0
    mock_pipeline_inst.run.assert_called_once_with(
        countries=["VN"],
        indicators=["NY.GDP.MKTP.CD"],
        start_year=2023,
        end_year=2023,
    )
    mock_minio.upload_dataframe.assert_called_once()


@pytest.mark.asyncio
async def test_main_no_command():
    """Test main function with no command."""
    # Arrange
    with patch("idp.ingestion.cli.create_parser") as mock_create_parser:
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = None
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser

        # Act
        result = await main([])

    # Assert
    assert result == 1
    mock_parser.print_help.assert_called_once()
