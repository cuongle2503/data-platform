"""World Bank Documents metadata fetching module."""

import logging
from typing import Any

from idp.common.exceptions import IngestionError
from idp.common.http_client import HttpClient

logger = logging.getLogger(__name__)


async def fetch_docs_metadata(
    http_client: HttpClient,
    country_code: str | None = None,
    topic: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    rows: int = 100,
    page: int = 1,
) -> dict[str, Any]:
    """Fetch document metadata from World Bank WDS API.

    Args:
        http_client: Configured HTTP client for the World Bank WDS API.
        country_code: ISO2 country code filter.
        topic: Topic filter.
        start_date: Start date filter (YYYY-MM-DD).
        end_date: End date filter (YYYY-MM-DD).
        rows: Number of results per page (max 100).
        page: Page number (1-indexed).

    Returns:
        Raw API response containing documents and pagination metadata.

    Raises:
        IngestionError: If the API request fails or returns unexpected format.
    """
    endpoint = ""
    params: dict[str, Any] = {
        "format": "json",
        "rows": min(rows, 100),
        "os": (page - 1) * rows,  # WDS uses offset (os) not page
        "fl": "id,docdt,count,display_title,docty,pdfurl,txturl,lang,url,theme,projn",
    }

    if country_code:
        params["countcode"] = country_code

    if topic:
        params["topic"] = topic

    if start_date and end_date:
        params["docdt"] = f"[{start_date}T00:00:00Z TO {end_date}T23:59:59Z]"
    elif start_date:
        params["docdt"] = f"[{start_date}T00:00:00Z TO *]"

    try:
        response_data = await http_client.get(endpoint, params=params)

        if not isinstance(response_data, dict):
            raise IngestionError("Unexpected WDS API response format")

        if "documents" not in response_data:
            raise IngestionError("WDS API response missing 'documents' field")

        logger.info(
            f"Fetched {len(response_data.get('documents', {}))} documents "
            f"(page {page}, total: {response_data.get('total', 0)})"
        )
        return response_data

    except Exception as e:
        if isinstance(e, IngestionError):
            raise
        raise IngestionError(f"Failed to fetch documents metadata: {e!s}") from e


async def fetch_all_docs_metadata(
    http_client: HttpClient,
    country_code: str | None = None,
    topic: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    max_pages: int | None = None,
) -> list[dict[str, Any]]:
    """Fetch all document metadata with automatic pagination.

    Args:
        http_client: Configured HTTP client.
        country_code: ISO2 country code filter.
        topic: Topic filter.
        start_date: Start date filter (YYYY-MM-DD).
        end_date: End date filter (YYYY-MM-DD).
        max_pages: Maximum number of pages to fetch (None = all).

    Returns:
        List of all document records.
    """
    all_documents = []
    page = 1
    rows_per_page = 100

    while True:
        response = await fetch_docs_metadata(
            http_client=http_client,
            country_code=country_code,
            topic=topic,
            start_date=start_date,
            end_date=end_date,
            rows=rows_per_page,
            page=page,
        )

        documents = response.get("documents", {})
        if not documents:
            break

        # Convert dict of documents to list
        all_documents.extend(documents.values())

        # Check if we've reached the end or max_pages limit
        total = response.get("total", 0)
        fetched_so_far = page * rows_per_page

        if fetched_so_far >= total:
            break

        if max_pages and page >= max_pages:
            logger.info(f"Reached max_pages limit: {max_pages}")
            break

        page += 1

    logger.info(f"Fetched total of {len(all_documents)} documents")
    return all_documents
