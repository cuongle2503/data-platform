"""CLI interface for data ingestion commands."""

import argparse
import logging

import polars as pl

from idp.common.config import get_settings
from idp.common.minio_client import MinioClient
from idp.ingestion.world_bank.docs_pipeline import WorldBankDocsPipeline
from idp.ingestion.world_bank.pipeline import WorldBankIndicatorsPipeline

logger = logging.getLogger(__name__)


def _minio_client_from_settings() -> MinioClient:
    """Create a MinioClient from current settings."""
    settings = get_settings()
    return MinioClient(
        endpoint=settings.minio.endpoint,
        access_key=settings.minio.access_key,
        secret_key=settings.minio.secret_key,
        secure=settings.minio.secure,
        bucket_name=settings.minio.bucket_bronze,
    )


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
    docs_parser = subparsers.add_parser(
        "ingest-docs-metadata",
        help="Fetch World Bank document metadata",
    )
    docs_parser.add_argument(
        "--countries",
        type=str,
        default=None,
        help="Comma-separated list of country codes (e.g., VN,CN)",
    )
    docs_parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Topic filter for documents",
    )
    docs_parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Start date (YYYY-MM-DD)",
    )
    docs_parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD)",
    )
    docs_parser.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Max pages per country to fetch (default: 1)",
    )

    # ingest-docs-text command
    docs_text_parser = subparsers.add_parser(
        "ingest-docs-text",
        help="Fetch World Bank document text and chunk it",
    )
    docs_text_parser.add_argument(
        "--doc-id",
        type=str,
        default=None,
        help="Single document ID to fetch and chunk",
    )
    docs_text_parser.add_argument(
        "--txt-url",
        type=str,
        default=None,
        help="Text URL for the document (required if --doc-id is set)",
    )
    docs_text_parser.add_argument(
        "--chunk-size",
        type=int,
        default=1500,
        help="Max characters per chunk (default: 1500)",
    )
    docs_text_parser.add_argument(
        "--overlap",
        type=int,
        default=150,
        help="Overlap between chunks (default: 150)",
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
            return await _run_docs_ingestion(args)
        elif args.command == "ingest-docs-text":
            return await _run_docs_text_ingestion(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        logger.error(f"Ingestion failed: {e!s}")
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
    minio_client = _minio_client_from_settings()
    df = pl.DataFrame(records)
    path = minio_client.upload_dataframe(df, "world_bank/indicators/data.parquet")
    logger.info(f"Uploaded {len(records)} records to {path}")

    return 0


async def _run_docs_ingestion(args: argparse.Namespace) -> int:
    """Run World Bank documents metadata ingestion.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    settings = get_settings()

    # Parse country filters
    countries: list[str] | None = None
    if args.countries:
        countries = [c.strip() for c in args.countries.split(",")]

    logger.info(
        f"Starting docs metadata ingestion: "
        f"countries={countries or 'default'}, "
        f"topic={args.topic or 'all'}, "
        f"dates={args.start_date or 'any'} to {args.end_date or 'any'}, "
        f"max_pages={args.max_pages}"
    )

    async with WorldBankDocsPipeline(settings=settings) as pipeline:
        records = await pipeline.run(
            countries=countries,
            topic=args.topic,
            start_date=args.start_date,
            end_date=args.end_date,
            max_pages_per_country=args.max_pages,
        )

    if not records:
        logger.info("No document records fetched.")
        return 0

    # Upload to MinIO
    minio_client = _minio_client_from_settings()
    df = pl.DataFrame(records)
    path = minio_client.upload_dataframe(df, "world_bank/docs/metadata/data.parquet")
    logger.info(f"Uploaded {len(records)} document records to {path}")

    return 0


async def _run_docs_text_ingestion(args: argparse.Namespace) -> int:
    """Run World Bank document text extraction and chunking.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    from idp.common.http_client import HttpClient
    from idp.ingestion.world_bank.bronze_schema import validate_chunks_records
    from idp.ingestion.world_bank.docs_text import fetch_and_chunk_doc

    settings = get_settings()

    if not args.doc_id or not args.txt_url:
        logger.error("--doc-id and --txt-url are required for text extraction")
        return 1

    logger.info(
        f"Starting text extraction: doc_id={args.doc_id}, "
        f"chunk_size={args.chunk_size}, overlap={args.overlap}"
    )

    http_client = HttpClient(
        base_url="",
        rate_limit=5,
        max_retries=3,
        proxies=settings.proxy.get_proxies(),
    )

    try:
        chunk_records = await fetch_and_chunk_doc(
            doc_id=args.doc_id,
            txt_url=args.txt_url,
            http_client=http_client,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
        )
    finally:
        await http_client.aclose()

    if not chunk_records:
        logger.info("No chunks generated.")
        return 0

    valid_records = validate_chunks_records(chunk_records)
    logger.info(f"Generated {len(valid_records)} valid chunks")

    # Upload to MinIO
    minio_client = _minio_client_from_settings()
    df = pl.DataFrame(valid_records)
    path = minio_client.upload_dataframe(df, f"world_bank/docs/chunks/{args.doc_id}/data.parquet")
    logger.info(f"Uploaded {len(valid_records)} chunks to {path}")

    return 0
