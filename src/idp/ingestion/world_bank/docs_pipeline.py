"""World Bank documents metadata ingestion pipeline."""

import logging
from datetime import UTC, datetime
from typing import Any

from idp.common.config import Settings, get_settings
from idp.common.exceptions import IngestionError
from idp.common.http_client import HttpClient
from idp.ingestion.world_bank.bronze_schema import validate_docs_records
from idp.ingestion.world_bank.docs_metadata import fetch_all_docs_metadata

logger = logging.getLogger(__name__)


class WorldBankDocsPipeline:
    """Pipeline for fetching and storing World Bank document metadata into MinIO Bronze."""

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: HttpClient | None = None,
    ) -> None:
        """Initialize the pipeline.

        Args:
            settings: Application settings. Uses cached instance if not provided.
            http_client: Optional HTTP client for testing. Creates new if not provided.
        """
        self.settings = settings or get_settings()

        self._http_client = http_client
        self._owns_http_client = http_client is None

    @property
    def http_client(self) -> HttpClient:
        """Get or create the HTTP client instance."""
        if self._http_client is None:
            self._http_client = HttpClient(
                base_url=self.settings.world_bank.wds_url,
                rate_limit=10,
                max_retries=3,
                proxies=self.settings.proxy.get_proxies(),
            )
        return self._http_client

    async def close(self) -> None:
        """Clean up resources."""
        if self._owns_http_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> "WorldBankDocsPipeline":
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        await self.close()

    def normalize_doc_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize a WDS API document record into bronze schema format.

        Args:
            record: Raw WDS API document.

        Returns:
            Normalized record matching the docs metadata bronze schema.
        """
        # Extract titles from nested docna dict
        title = ""
        docna = record.get("docna", {})
        if isinstance(docna, dict):
            # docna is a dict with string keys; get first non-empty value
            for key in sorted(docna.keys(), key=lambda k: int(k) if k.isdigit() else 0):
                entry = docna[key]
                title = entry.get("docna", "") if isinstance(entry, dict) else str(entry)
                if title:
                    break

        # Fallback to display_title
        if not title:
            title = record.get("display_title", "")

        # Extract topics from comma-separated string
        topics_raw = record.get("theme", "")
        topics: list[str] = []
        if topics_raw:
            topics = [t.strip() for t in topics_raw.split(",") if t.strip()]

        # Extract country list
        countries_raw = record.get("count", "")
        countries: list[str] = [countries_raw] if countries_raw else []

        return {
            "doc_id": record.get("id", ""),
            "title": title,
            "abstract": record.get("abstract", ""),
            "display_date": record.get("docdt"),
            "doc_type": record.get("docty", ""),
            "pdf_url": record.get("pdfurl", ""),
            "txt_url": record.get("txturl", ""),
            "countries": countries,
            "topics": topics,
            "language": record.get("lang", ""),
            "ingested_at": datetime.now(UTC),
            "source": "world_bank_wds_api",
        }

    async def fetch_metadata(
        self,
        country_code: str,
        topic: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        max_pages: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch and normalize document metadata for a country.

        Args:
            country_code: ISO2 country code.
            topic: Optional topic filter.
            start_date: Optional start date filter (YYYY-MM-DD).
            end_date: Optional end date filter (YYYY-MM-DD).
            max_pages: Optional max pages limit.

        Returns:
            List of normalized document records.
        """
        try:
            raw_docs = await fetch_all_docs_metadata(
                http_client=self.http_client,
                country_code=country_code,
                topic=topic,
                start_date=start_date,
                end_date=end_date,
                max_pages=max_pages,
            )

            normalized = [self.normalize_doc_record(r) for r in raw_docs]
            valid_records = validate_docs_records(normalized)

            logger.info(
                f"Normalized {len(valid_records)} valid docs for {country_code}"
            )
            return valid_records

        except IngestionError as e:
            logger.warning(f"Ingestion error for docs/{country_code}: {e!s}")
            return []
        except Exception as e:
            logger.error(f"Error fetching docs for {country_code}: {e!s}")
            return []

    async def run(
        self,
        countries: list[str] | None = None,
        topic: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        max_pages_per_country: int = 1,
    ) -> list[dict[str, Any]]:
        """Run the full document metadata ingestion pipeline for multiple countries.

        Args:
            countries: List of country codes (defaults from config).
            topic: Optional topic filter.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            max_pages_per_country: Max pages per country (default 1 for sampling).

        Returns:
            List of all fetched and normalized document metadata records.
        """
        from idp.common.config import get_wb_countries

        country_list = get_wb_countries(countries)

        all_records = []

        for country in country_list:
            code = country["code"]
            logger.info(f"Fetching docs metadata for {country['name']} ({code})")

            records = await self.fetch_metadata(
                country_code=code,
                topic=topic,
                start_date=start_date,
                end_date=end_date,
                max_pages=max_pages_per_country,
            )

            all_records.extend(records)

        logger.info(f"Docs pipeline complete: {len(all_records)} total records")
        return all_records
