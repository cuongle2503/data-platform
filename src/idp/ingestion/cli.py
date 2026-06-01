"""CLI interface for data ingestion commands."""

import argparse
import asyncio
import logging
import sys
from typing import Any

import polars as pl

from idp.common.minio_client import MinioClient
from idp.common.config import get_settings, get_wb_indicators
from idp.ingestion.world_bank.pipeline import WorldBankIndicatorsPipeline

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for ingestion CLI commands.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="idp-ingest",
        description="IDP Data Ingestion CLI — fetch and store data from external sources",
    )

    subparsers = parser.add_subparsers(dest="command", help="Ingestion commands")

    # ingest-indicators command
    indicators_parser = subparsers.add_parser(
        "ingest-indicators",
        help="Fetch World Bank indicator data",
    )
    indicators_parser.add_argument(
        "--countries",
        type=str,
        default=None,
        help="Comma-separated list of country codes (e.g., VN,CN,JP)",
    )
    indicators_parser.add_argument(
        "--indicators",
        type=str,
        default=None,
        help="Comma-separated list of indicator codes",
    )
    indicators_parser.add_argument(
        "--start-year",
        type=int,
        default=None,
        help="Start year for data (default: 2010)",
    )
    indicators_parser.add_argument(
        "--end-year",
        type=int,
        default=None,
        help="End year for data (default: current year)",
    )

    # ingest-docs-metadata command
    subparsers.add_parser(
        "ingest-docs-metadata",
        help="Fetch World Bank document metadata (not yet implemented)",
    )

    return parser


async def main(argv: list[str] | None = None) -> int:
    """Main entry point for the ingestion CLI.

    Args:
        argv: Command-line arguments. Uses sys.argv if None.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "ingest-indicators":
            return await _run_indicators_ingestion(args)
        elif args.command == "ingest-docs-metadata":
            logger.info("Document metadata ingestion is not yet implemented.")
            return 0
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        return 1


async def _run_indicators_ingestion(args: argparse.Namespace) -> int:
    """Run World Bank indicators ingestion.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    settings = get_settings()

    # Parse country/indicator filters
    countries: list[str] | None = None
    if args.countries:
        countries = [c.strip() for c in args.countries.split(",")]

    indicators: list[str] | None = None
    if args.indicators:
        indicators = [i.strip() for i in args.indicators.split(",")]

    logger.info(
        f"Starting indicators ingestion: "
        f"countries={countries or 'default'}, "
        f"indicators={indicators or 'default'}, "
        f"years={args.start_year or settings.world_bank.default_start_year}-{args.end_year or 'now'}"
    )

    async with WorldBankIndicatorsPipeline(settings=settings) as pipeline:
        records = await pipeline.run(
            countries=countries,
            indicators=indicators,
            start_year=args.start_year or settings.world_bank.default_start_year,
            end_year=args.end_year,
        )

    if not records:
        logger.info("No records fetched.")
        return 0

    # Upload to MinIO
    minio_client = MinioClient(
        endpoint=settings.minio.endpoint,
        access_key=settings.minio.access_key,
        secret_key=settings.minio.secret_key,
        secure=settings.minio.secure,
        bucket_name=settings.minio.bucket_bronze,
    )

    df = pl.DataFrame(records)
    path = minio_client.upload_dataframe(df, "world_bank/indicators/data.parquet")
    logger.info(f"Uploaded {len(records)} records to {path}")

    return 0
