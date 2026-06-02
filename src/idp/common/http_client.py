"""HTTP client with robust retry and rate limiting capabilities."""

import asyncio
import logging
import time
from typing import Any

import httpx

from idp.common.exceptions import IngestionError

logger = logging.getLogger(__name__)


class HttpClient:
    """Robust HTTP client for external API communication."""

    def __init__(
        self,
        base_url: str,
        rate_limit: int = 10,
        max_retries: int = 3,
        timeout: float = 30.0,
        proxies: dict[str, str] | None = None,
    ) -> None:
        """Initialize HTTP client.

        Args:
            base_url: Base URL for all requests.
            rate_limit: Maximum requests per second.
            max_retries: Maximum number of retries for failed requests.
            timeout: Request timeout in seconds.
            proxies: Dictionary of proxy URLs.
        """
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.timeout = timeout

        # Calculate minimum time between requests to satisfy rate limit
        self._min_request_interval = 1.0 / rate_limit if rate_limit > 0 else 0
        self._last_request_time = 0.0

        # Initialize underlying client
        client_kwargs: dict[str, Any] = {
            "base_url": base_url,
            "timeout": timeout,
            "follow_redirects": True,
        }

        # Handle proxy configuration via mounts for httpx
        if proxies:
            proxy_mounts: dict[str, httpx.AsyncHTTPTransport | None] = {}
            for scheme, proxy_url in proxies.items():
                if proxy_url:
                    proxy_transport = httpx.AsyncHTTPTransport(proxy=proxy_url)
                    proxy_mounts[scheme] = proxy_transport
            if proxy_mounts:
                client_kwargs["mounts"] = proxy_mounts

        self._client = httpx.AsyncClient(**client_kwargs)

    async def __aenter__(self) -> "HttpClient":
        """Support context manager protocol."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close client on context exit."""
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def _wait_for_rate_limit(self) -> None:
        """Pause execution if necessary to respect rate limits."""
        now = time.monotonic()
        time_since_last = now - self._last_request_time

        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self._last_request_time = time.monotonic()

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Perform a GET request with retries and rate limiting.

        Args:
            endpoint: URL path relative to base_url.
            params: Query parameters.

        Returns:
            JSON response payload.

        Raises:
            IngestionError: If the request fails after max retries.
        """
        attempt = 0
        last_error = None

        while attempt <= self.max_retries:
            try:
                await self._wait_for_rate_limit()

                response = await self._client.get(endpoint, params=params)

                # Check for HTTP errors (4xx, 5xx)
                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(
                    f"HTTP error on attempt {attempt + 1}/{self.max_retries + 1}: "
                    f"{e.response.status_code} - {e.response.text}"
                )

                # Don't retry on client errors (except 429 Too Many Requests)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise IngestionError(f"Client error: {e.response.status_code}") from e

            except httpx.RequestError as e:
                last_error = e
                logger.warning(
                    f"Network error on attempt {attempt + 1}/{self.max_retries + 1}: {e!s}"
                )

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error during GET request: {e!s}")
                break

            attempt += 1
            if attempt <= self.max_retries:
                # Exponential backoff: 1s, 2s, 4s...
                backoff = 2 ** (attempt - 1)
                logger.info(f"Retrying in {backoff} seconds...")
                await asyncio.sleep(backoff)

        raise IngestionError(
            f"HTTP request failed after {self.max_retries} retries. Last error: {last_error!s}"
        ) from last_error
