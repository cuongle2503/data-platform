"""Unit tests for HTTP client with retry and rate limiting."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from idp.common.exceptions import IngestionError
from idp.common.http_client import HttpClient


@pytest.mark.asyncio
async def test_get_success():
    """Test successful GET request."""
    # Arrange
    client = HttpClient(base_url="https://api.example.com", rate_limit=10)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}

    # Act
    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await client.get("/endpoint")

    # Assert
    assert result == {"data": "test"}
    mock_get.assert_called_once_with("/endpoint", params=None)


@pytest.mark.asyncio
async def test_get_with_params():
    """Test GET request with query parameters."""
    # Arrange
    client = HttpClient(base_url="https://api.example.com")
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}

    # Act
    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await client.get("/search", params={"q": "test", "page": 1})

    # Assert
    assert result == {"results": []}
    mock_get.assert_called_once_with("/search", params={"q": "test", "page": 1})


@pytest.mark.asyncio
async def test_get_retry_on_500_error():
    """Test retry mechanism on 500 server error."""
    # Arrange
    client = HttpClient(base_url="https://api.example.com", max_retries=3)
    mock_response_fail = Mock()
    mock_response_fail.status_code = 500
    mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=Mock(), response=mock_response_fail
    )

    mock_response_success = Mock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {"data": "recovered"}

    # Act
    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        # First 2 calls fail, 3rd succeeds
        mock_get.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success,
        ]
        result = await client.get("/endpoint")

    # Assert
    assert result == {"data": "recovered"}
    assert mock_get.call_count == 3


@pytest.mark.asyncio
async def test_get_raises_after_max_retries():
    """Test that IngestionError is raised after max retries exhausted."""
    # Arrange
    client = HttpClient(base_url="https://api.example.com", max_retries=2)
    mock_response = Mock()
    mock_response.status_code = 503
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Service Unavailable", request=Mock(), response=mock_response
    )

    # Act & Assert
    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        with pytest.raises(IngestionError, match="HTTP request failed after 2 retries"):
            await client.get("/endpoint")


@pytest.mark.asyncio
async def test_get_handles_network_error():
    """Test handling of network errors."""
    # Arrange
    client = HttpClient(base_url="https://api.example.com", max_retries=1)

    # Act & Assert
    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection failed")
        with pytest.raises(IngestionError, match="HTTP request failed"):
            await client.get("/endpoint")


@pytest.mark.asyncio
async def test_rate_limiting_delays_requests():
    """Test that rate limiting adds delays between requests."""
    # Arrange
    client = HttpClient(base_url="https://api.example.com", rate_limit=10)  # 10 req/s
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}

    # Act
    with (
        patch.object(client._client, "get", new_callable=AsyncMock) as mock_get,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        mock_get.return_value = mock_response

        # Make 3 requests
        await client.get("/endpoint1")
        await client.get("/endpoint2")
        await client.get("/endpoint3")

    # Assert - should have 2 sleep calls (not before first request)
    assert mock_sleep.call_count == 2


@pytest.mark.asyncio
async def test_context_manager_closes_client():
    """Test that context manager properly closes the HTTP client."""
    # Arrange & Act
    async with HttpClient(base_url="https://api.example.com") as client:
        assert client._client is not None

    # Assert - client should be closed after context exit
    # (We can't directly test this without accessing internals, but we verify no errors)


@pytest.mark.asyncio
async def test_get_with_empty_response():
    """Test handling of empty JSON response."""
    # Arrange
    client = HttpClient(base_url="https://api.example.com")
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = None

    # Act
    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await client.get("/endpoint")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_client_with_proxies():
    """Test client initialization with proxies."""
    # Arrange
    proxies = {"http://": "http://proxy:8080", "https://": "http://proxy:8080"}

    # Act
    client = HttpClient(base_url="https://api.example.com", proxies=proxies)

    # Assert
    assert client._client is not None
    # Just verifying it initializes without error


@pytest.mark.asyncio
async def test_get_handles_unexpected_error():
    """Test handling of unexpected errors."""
    # Arrange
    client = HttpClient(base_url="https://api.example.com", max_retries=1)

    # Act & Assert
    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = ValueError("Unexpected issue")
        with pytest.raises(IngestionError, match="HTTP request failed"):
            await client.get("/endpoint")
