"""Main entry point for IDP."""

import asyncio
import sys

from idp.common.logging_config import setup_logging
from idp.ingestion.cli import main as ingestion_main


def main() -> int:
    """Main application entry point."""
    setup_logging()

    # Determine which subcommand group to run
    # Currently we only have ingestion commands
    if len(sys.argv) > 1 and sys.argv[1].startswith("ingest-"):
        return asyncio.run(ingestion_main(sys.argv[1:]))

    # For now, default to showing ingestion help if no args
    if len(sys.argv) == 1:
        return asyncio.run(ingestion_main(["--help"]))

    print(f"Unknown command group: {sys.argv[1]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
