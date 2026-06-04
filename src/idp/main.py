"""Main entry point for IDP."""

import asyncio
import logging
import sys

from idp.common.logging_config import setup_logging
from idp.ingestion.cli import main as ingestion_main

logger = logging.getLogger(__name__)


def main() -> int:
    """Main application entry point."""
    setup_logging()

    # Determine which subcommand group to run
    if len(sys.argv) > 1 and sys.argv[1].startswith("ingest-"):
        return asyncio.run(ingestion_main(sys.argv[1:]))

    # Default to showing ingestion help if no args
    if len(sys.argv) == 1:
        return asyncio.run(ingestion_main(["--help"]))

    logger.error("Unknown command group: %s", sys.argv[1])
    return 1


if __name__ == "__main__":
    sys.exit(main())
