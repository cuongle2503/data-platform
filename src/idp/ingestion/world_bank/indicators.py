"""World Bank Indicators fetching module."""

import asyncio
import logging
from typing import Any

from idp.common.http_client import HttpClient
from idp.common.exceptions import IngestionError

logger = logging.getLogger(__name__)


async def fetch_indicator_data(
    http_client: HttpClient,
    country_code: str,
    indicator_code: str,
    start_year: int | None = None,
    end_year: int | None = None,
) -> list[dict[str, Any]]:
    """Fetch data for a specific indicator and country.

    Handles pagination automatically.

    Args:
        http_client: Configured HTTP client for the World Bank API.
        country_code: ISO2 or ISO3 country code.
        indicator_code: World Bank indicator code.
        start_year: Optional start year filter.
        end_year: Optional end year filter.

    Returns:
        List of raw indicator records from the API.

    Raises:
        IngestionError: If the API request fails or returns unexpected format.
    """
    endpoint = f"/country/{country_code}/indicator/{indicator_code}"
    params: dict[str, Any] = {"format": "json"}

    if start_year and end_year:
        params["date"] = f"{start_year}:{end_year}"
    elif start_year:
        params["date"] = str(start_year)

    all_records = []
    page = 1
    total_pages = 1

    try:
        while page <= total_pages:
            params["page"] = page

            response_data = await http_client.get(endpoint, params=params)

            # World Bank API returns a list where [0] is metadata, [1] is data
            if not isinstance(response_data, list) or len(response_data) != 2:
                raise IngestionError(f"Unexpected API response format for {indicator_code}")

            meta, data = response_data

            if data:
                all_records.extend(data)

            # Update pagination info
            if "pages" in meta:
                total_pages = meta["pages"]
            else:
                break

            page += 1

        logger.info(f"Fetched {len(all_records)} records for {country_code}/{indicator_code}")
        return all_records

    except Exception as e:
        if isinstance(e, IngestionError):
            raise
        raise IngestionError(
            f"Failed to fetch indicator data {indicator_code} for {country_code}: {str(e)}"
        ) from e


async def fetch_multiple_indicators(
    http_client: HttpClient,
    country_code: str,
    indicators: list[dict[str, str]],
    start_year: int | None = None,
    end_year: int | None = None,
) -> list[dict[str, Any]]:
    """Fetch multiple indicators concurrently for a country.

    Args:
        http_client: Configured HTTP client.
        country_code: Country code.
        indicators: List of indicator definition dicts.
        start_year: Optional start year filter.
        end_year: Optional end year filter.

    Returns:
        Combined list of all raw indicator records.
    """
    tasks = []

    for indicator in indicators:
        code = indicator["code"]
        task = fetch_indicator_data(
            http_client=http_client,
            country_code=country_code,
            indicator_code=code,
            start_year=start_year,
            end_year=end_year,
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_records = []
    for i, result in enumerate(results):
        indicator_code = indicators[i]["code"]
        if isinstance(result, Exception):
            logger.error(f"Failed to fetch indicator {indicator_code}: {str(result)}")
        else:
            all_records.extend(result)

    return all_records
