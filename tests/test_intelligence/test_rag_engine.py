"""Tests for RAG engine components."""

from idp.intelligence.context_builder import build_context
from idp.intelligence.query_parser import extract_entities, normalize_query


class TestQueryParser:
    """Test query parsing and entity extraction."""

    def test_normalize_query_basic(self):
        """Should normalize query to lowercase and strip whitespace."""
        # Arrange & Act
        result = normalize_query("  What is GDP of Vietnam?  ")

        # Assert
        assert result == "what is gdp of vietnam?"

    def test_extract_entities_country_codes(self):
        """Should extract country codes from query."""
        # Arrange & Act
        entities = extract_entities("What is the GDP of VNM and THA in 2023?")

        # Assert
        assert "VNM" in entities["country_codes"]
        assert "THA" in entities["country_codes"]

    def test_extract_entities_years(self):
        """Should extract years from query."""
        # Arrange & Act
        entities = extract_entities("Compare GDP in 2020, 2021, and 2023")

        # Assert
        assert 2020 in entities["years"]
        assert 2021 in entities["years"]
        assert 2023 in entities["years"]

    def test_extract_entities_no_matches(self):
        """Should return empty lists when no entities found."""
        # Arrange & Act
        entities = extract_entities("What is economic growth?")

        # Assert
        assert entities["country_codes"] == []
        assert entities["years"] == []


class TestContextBuilder:
    """Test context building for RAG."""

    def test_build_context_with_indicators(self):
        """Should format indicators and data into markdown context."""
        # Arrange
        indicators = [
            {
                "indicator_code": "NY.GDP.MKTP.CD",
                "indicator_name": "GDP (current US$)",
                "description": "GDP at purchaser's prices",
            }
        ]
        timeseries_data = [
            {
                "country_code": "VNM",
                "indicator_code": "NY.GDP.MKTP.CD",
                "year": 2023,
                "value": 429.7,
            }
        ]

        # Act
        context = build_context(indicators, timeseries_data)

        # Assert
        assert "NY.GDP.MKTP.CD" in context
        assert "GDP (current US$)" in context
        assert "VNM" in context
        assert "2023" in context
        assert "429.7" in context

    def test_build_context_empty_data(self):
        """Should handle empty data gracefully."""
        # Arrange & Act
        context = build_context([], [])

        # Assert
        assert "No data available" in context or context == ""
