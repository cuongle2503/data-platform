from unittest.mock import MagicMock

import pytest

from idp.storage.repository import StorageRepository


@pytest.fixture
def mock_conn():
    conn = MagicMock()
    conn.cursor.return_value = MagicMock()
    return conn


@pytest.fixture
def repo(mock_conn):
    return StorageRepository(mock_conn)


def test_get_countries_returns_empty_list(repo, mock_conn):
    # Arrange
    cursor = mock_conn.cursor.return_value
    cursor.fetchall.return_value = []

    # Act
    result = repo.get_countries()

    # Assert
    assert result == []
    cursor.execute.assert_called_once()


def test_get_countries_returns_list(repo, mock_conn):
    # Arrange
    cursor = mock_conn.cursor.return_value
    cursor.fetchall.return_value = [
        ("VNM", "Viet Nam", "East Asia & Pacific", "Lower middle income", True, True),
        ("JPN", "Japan", "East Asia & Pacific", "High income", False, True),
    ]

    # Act
    result = repo.get_countries()

    # Assert
    assert len(result) == 2
    assert result[0]["country_code"] == "VNM"
    assert result[0]["country_name"] == "Viet Nam"


def test_get_country_returns_none_when_not_found(repo, mock_conn):
    # Arrange
    cursor = mock_conn.cursor.return_value
    cursor.fetchone.return_value = None

    # Act
    result = repo.get_country("ZZZ")

    # Assert
    assert result is None


def test_get_indicators_returns_list(repo, mock_conn):
    # Arrange
    cursor = mock_conn.cursor.return_value
    cursor.fetchall.return_value = [
        ("NY.GDP.MKTP.CD", "GDP (current US$)", "gdp", "USD", "Gross Domestic Product"),
    ]

    # Act
    result = repo.get_indicators()

    # Assert
    assert len(result) == 1
    assert result[0]["indicator_code"] == "NY.GDP.MKTP.CD"


def test_get_indicator_returns_none_when_not_found(repo, mock_conn):
    # Arrange
    cursor = mock_conn.cursor.return_value
    cursor.fetchone.return_value = None

    # Act
    result = repo.get_indicator("INVALID.CODE")

    # Assert
    assert result is None


def test_get_timeseries_returns_list(repo, mock_conn):
    # Arrange
    cursor = mock_conn.cursor.return_value
    cursor.fetchall.return_value = [
        ("VNM", "GDP", "2020", 100.0, "world_bank_api"),
        ("VNM", "GDP", "2021", 110.0, "world_bank_api"),
    ]

    # Act
    result = repo.get_timeseries("VNM", ["GDP"], [2020, 2021])

    # Assert
    assert len(result) == 2
    assert result[0]["value"] == 100.0


def test_get_timeseries_returns_empty_when_no_data(repo, mock_conn):
    # Arrange
    cursor = mock_conn.cursor.return_value
    cursor.fetchall.return_value = []

    # Act
    result = repo.get_timeseries("ZZZ", ["NONE"], None)

    # Assert
    assert result == []


def test_search_indicators_lexical_returns_matches(repo, mock_conn):
    # Arrange
    cursor = mock_conn.cursor.return_value
    cursor.fetchall.return_value = [
        (
            "NY.GDP.MKTP.CD",
            "GDP (current US$)",
            "Gross Domestic Product at purchaser's prices",
            "gdp",
        ),
    ]

    # Act
    result = repo.search_indicators_lexical("gdp")

    # Assert
    assert len(result) == 1
    cursor.execute.assert_called_once()


def test_search_indicators_semantic_returns_matches(repo, mock_conn):
    # Arrange
    cursor = mock_conn.cursor.return_value
    query_embedding = [0.1, 0.2, 0.3]
    cursor.fetchall.return_value = [
        ("NY.GDP.MKTP.CD", "GDP (current US$)", "gdp", 0.95),
    ]

    # Act
    result = repo.search_indicators_semantic(query_embedding, limit=5)

    # Assert
    assert len(result) == 1
    assert result[0]["similarity"] == 0.95
