"""World Bank indicators ingestion pipeline."""

import logging
from datetime import UTC, datetime
from typing import Any

from idp.common.config import Settings, get_settings
from idp.common.exceptions import IngestionError
from idp.common.http_client import HttpClient
from idp.ingestion.world_bank.bronze_schema import validate_records
from idp.ingestion.world_bank.indicators import fetch_indicator_data, fetch_multiple_indicators

logger = logging.getLogger(__name__)


class WorldBankIndicatorsPipeline:
    """Pipeline for fetching and storing World Bank indicator data into MinIO Bronze."""

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
                base_url=self.settings.world_bank.api_url,
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

    async def __aenter__(self) -> "WorldBankIndicatorsPipeline":
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        await self.close()

    def normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize a World Bank API record into bronze schema format.

        Args:
            record: Raw API record.

        Returns:
            Normalized record matching the bronze schema.
        """
        return {
            "country_code": record.get("countryiso3code", ""),
            "country_name": record.get("country", {}).get("value", ""),
            "indicator_code": record.get("indicator", {}).get("id", ""),
            "indicator_name": record.get("indicator", {}).get("value", ""),
            "year": int(record["date"]),
            "value": float(record["value"]) if record["value"] is not None else None,
            "ingested_at": datetime.now(UTC),
            "source": "world_bank_api",
        }

    async def fetch_indicator(
        self,
        country_code: str,
        indicator_code: str,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch and normalize indicator data.

        Args:
            country_code: ISO2/ISO3 country code.
            indicator_code: World Bank indicator code.
            start_year: Optional start year filter.
            end_year: Optional end year filter.

        Returns:
            List of normalized records.
        """
        try:
            raw_records = await fetch_indicator_data(
                http_client=self.http_client,
                country_code=country_code,
                indicator_code=indicator_code,
                start_year=start_year,
                end_year=end_year,
            )

            normalized = [self.normalize_record(r) for r in raw_records]
            valid_records = validate_records(normalized)

            return valid_records

        except IngestionError as e:
            logger.warning(f"Ingestion error for {indicator_code}/{country_code}: {e!s}")
            return []
        except Exception as e:
            logger.error(f"Error fetching {indicator_code} for {country_code}: {e!s}")
            return []

    async def run(
        self,
        countries: list[str] | None = None,
        indicators: list[str] | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Run the full ingestion pipeline for multiple countries and indicators.

        Args:
            countries: List of country codes (defaults from config).
            indicators: List of indicator codes (defaults from config).
            start_year: Optional start year.
            end_year: Optional end year.

        Returns:
            List of all fetched and normalized records.
        """
        from idp.common.config import get_wb_countries, get_wb_indicators

        country_list = get_wb_countries(countries)
        indicator_list = get_wb_indicators(indicators)

        all_records = []

        for country in country_list:
            code = country["code"]
            logger.info(f"Fetching indicators for {country['name']} ({code})")

            records = await fetch_multiple_indicators(
                http_client=self.http_client,
                country_code=code,
                indicators=indicator_list,
                start_year=start_year,
                end_year=end_year,
            )

            normalized = [self.normalize_record(r) for r in records]
            valid = validate_records(normalized)
            all_records.extend(valid)

        logger.info(f"Pipeline complete: {len(all_records)} total records")
        return all_records
