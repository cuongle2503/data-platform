from unittest.mock import MagicMock

from idp.storage.generate_indicator_embeddings import build_indicator_text, get_existing_ref_ids


def test_build_indicator_text_with_full_data():
    # Arrange
    row = {
        "indicator_code": "NY.GDP.MKTP.CD",
        "indicator_name": "GDP (current US$)",
        "category": "gdp",
        "unit": "USD",
        "description": "Gross Domestic Product at purchaser's prices",
    }

    # Act
    result = build_indicator_text(row)

    # Assert
    assert "Indicator: GDP (current US$)" in result
    assert "Code: NY.GDP.MKTP.CD" in result
    assert "Category: gdp" in result
    assert "Unit: USD" in result
    assert "Gross Domestic Product" in result


def test_build_indicator_text_with_missing_fields():
    # Arrange
    row = {
        "indicator_code": "SP.POP.TOTL",
        "indicator_name": "Population, total",
        "category": None,
        "unit": None,
        "description": None,
    }

    # Act
    result = build_indicator_text(row)

    # Assert
    assert "Indicator: Population, total" in result
    assert "Code: SP.POP.TOTL" in result
    assert "Category: N/A" in result
    assert "Unit: N/A" in result


def test_get_existing_ref_ids_returns_set():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("NY.GDP.MKTP.CD",),
        ("SP.POP.TOTL",),
    ]

    result = get_existing_ref_ids(mock_cursor, "economic_indicator")

    assert result == {"NY.GDP.MKTP.CD", "SP.POP.TOTL"}
    mock_cursor.execute.assert_called_once()


def test_get_existing_ref_ids_returns_empty_set():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []

    result = get_existing_ref_ids(mock_cursor, "economic_indicator")

    assert result == set()
