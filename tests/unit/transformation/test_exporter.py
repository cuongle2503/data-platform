"""Unit tests for DuckDB → PostgreSQL exporter."""

import datetime
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from idp.transformation.exporter import (
    GOLD_TABLES,
    _polars_to_postgres_type,
    export_gold_to_postgres,
)


class TestPolarsToPostgresType:
    """Tests for type mapping utility."""

    def test_maps_int32_to_bigint(self):
        assert _polars_to_postgres_type(pl.Int32) == "BIGINT"

    def test_maps_int64_to_bigint(self):
        assert _polars_to_postgres_type(pl.Int64) == "BIGINT"

    def test_maps_float64_to_double_precision(self):
        assert _polars_to_postgres_type(pl.Float64) == "DOUBLE PRECISION"

    def test_maps_boolean_to_boolean(self):
        assert _polars_to_postgres_type(pl.Boolean) == "BOOLEAN"

    def test_maps_datetime_to_timestamp(self):
        assert _polars_to_postgres_type(pl.Datetime) == "TIMESTAMP"

    def test_maps_date_to_date(self):
        assert _polars_to_postgres_type(pl.Date) == "DATE"

    def test_maps_utf8_to_text(self):
        assert _polars_to_postgres_type(pl.Utf8) == "TEXT"

    def test_maps_unknown_to_text(self):
        class FakeDtype:
            pass

        assert _polars_to_postgres_type(FakeDtype()) == "TEXT"


class TestExportGoldToPostgres:
    """Tests for the export function."""

    @pytest.fixture
    def sample_dim_countries(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "country_key": ["abc123", "def456"],
                "country_code": ["VN", "CN"],
                "country_name": ["Vietnam", "China"],
                "region": ["Asia", "Asia"],
                "income_group": ["Lower-middle", "Upper-middle"],
                "is_asean": [True, False],
                "is_primary": [True, False],
            }
        )

    @pytest.fixture
    def sample_dim_indicators(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "indicator_key": ["key001", "key002"],
                "indicator_code": ["NY.GDP.MKTP.CD", "SP.POP.TOTL"],
                "indicator_name": ["GDP (current US$)", "Population, total"],
                "source_system": ["WDI", "WDI"],
                "category": ["Economic", "Social"],
                "unit": ["Current US$", "Count"],
                "frequency": ["Annual", "Annual"],
                "description": ["Gross Domestic Product", "Total population"],
            }
        )

    @pytest.fixture
    def sample_dim_dates(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "date_key": ["d2020", "d2021"],
                "year": [2020, 2021],
                "decade": [2020, 2020],
                "century": [21, 21],
            }
        )

    @pytest.fixture
    def sample_fact(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "indicator_key": ["key001", "key002"],
                "country_key": ["abc123", "def456"],
                "date_key": ["d2020", "d2021"],
                "value": [362.6, 1412.0],
                "source": ["WDI", "WDI"],
                "loaded_at": [datetime.datetime(2026, 1, 1), datetime.datetime(2026, 1, 1)],
            }
        )

    @pytest.fixture
    def sample_data(self) -> dict[str, pl.DataFrame]:
        return {
            "dim_countries": pl.DataFrame(
                {
                    "country_key": ["abc123"],
                    "country_code": ["VN"],
                    "country_name": ["Vietnam"],
                    "region": ["Asia"],
                    "income_group": ["Lower-middle"],
                    "is_asean": [True],
                    "is_primary": [True],
                }
            ),
            "dim_indicators": pl.DataFrame(
                {
                    "indicator_key": ["key001"],
                    "indicator_code": ["NY.GDP.MKTP.CD"],
                    "indicator_name": ["GDP (current US$)"],
                    "source_system": ["WDI"],
                    "category": ["Economic"],
                    "unit": ["Current US$"],
                    "frequency": ["Annual"],
                    "description": ["Gross Domestic Product"],
                }
            ),
            "dim_dates": pl.DataFrame(
                {
                    "date_key": ["d2020"],
                    "year": [2020],
                    "decade": [2020],
                    "century": [21],
                }
            ),
            "fact_economic_indicators": pl.DataFrame(
                {
                    "indicator_key": ["key001"],
                    "country_key": ["abc123"],
                    "date_key": ["d2020"],
                    "value": [362.6],
                    "source": ["WDI"],
                    "loaded_at": [datetime.datetime(2026, 1, 1)],
                }
            ),
        }

    def test_export_creates_schema(
        self, mock_env: None, sample_data: dict[str, pl.DataFrame]
    ) -> None:
        """Verify schema creation SQL is executed."""
        mock_duckdb = MagicMock()
        mock_pg = MagicMock()
        mock_cursor = MagicMock()
        mock_pg.cursor.return_value.__enter__.return_value = mock_cursor

        with (
            patch("idp.transformation.exporter.duckdb.connect", return_value=mock_duckdb),
            patch("idp.transformation.exporter.psycopg.connect", return_value=mock_pg),
        ):
            # Simulate each table's data fetch
            mock_duckdb.execute.return_value.pl.side_effect = [
                sample_data["dim_countries"],
                sample_data["dim_indicators"],
                sample_data["dim_dates"],
                sample_data["fact_economic_indicators"],
            ]

            export_gold_to_postgres("test.duckdb", "gold")

        # Verify schema creation
        create_schema_calls = [
            call
            for call in mock_cursor.execute.call_args_list
            if "CREATE SCHEMA" in str(call)
        ]
        assert len(create_schema_calls) >= 1

    def test_export_handles_empty_table(
        self, mock_env: None, sample_data: dict[str, pl.DataFrame]
    ) -> None:
        """Verify empty tables are skipped gracefully."""
        mock_duckdb = MagicMock()
        mock_pg = MagicMock()
        mock_cursor = MagicMock()
        mock_pg.cursor.return_value.__enter__.return_value = mock_cursor

        # First table has data, others are empty
        mock_duckdb.execute.return_value.pl.side_effect = [
            sample_data["dim_countries"],
            pl.DataFrame(),  # empty dim_indicators
            pl.DataFrame(),  # empty dim_dates
            pl.DataFrame(),  # empty fact
        ]

        with (
            patch("idp.transformation.exporter.duckdb.connect", return_value=mock_duckdb),
            patch("idp.transformation.exporter.psycopg.connect", return_value=mock_pg),
        ):
            result = export_gold_to_postgres("test.duckdb", "gold")

        assert result["dim_countries"] == 1
        assert result["dim_indicators"] == 0
        assert result["dim_dates"] == 0
        assert result["fact_economic_indicators"] == 0

    def test_export_returns_row_counts(
        self, mock_env: None, sample_data: dict[str, pl.DataFrame]
    ) -> None:
        """Verify row counts are returned correctly."""
        mock_duckdb = MagicMock()
        mock_pg = MagicMock()
        mock_cursor = MagicMock()
        mock_pg.cursor.return_value.__enter__.return_value = mock_cursor

        mock_duckdb.execute.return_value.pl.side_effect = [
            sample_data["dim_countries"],
            sample_data["dim_indicators"],
            sample_data["dim_dates"],
            sample_data["fact_economic_indicators"],
        ]

        with (
            patch("idp.transformation.exporter.duckdb.connect", return_value=mock_duckdb),
            patch("idp.transformation.exporter.psycopg.connect", return_value=mock_pg),
        ):
            result = export_gold_to_postgres("test.duckdb", "gold")

        expected_rows = {table: len(sample_data[table]) for table in GOLD_TABLES}
        assert result == expected_rows

    def test_export_closes_connections(
        self, mock_env: None, sample_data: dict[str, pl.DataFrame]
    ) -> None:
        """Verify connections are closed even on error."""
        mock_duckdb = MagicMock()
        mock_pg = MagicMock()
        mock_cursor = MagicMock()
        mock_pg.cursor.return_value.__enter__.return_value = mock_cursor

        # Simulate error during export
        mock_duckdb.execute.side_effect = RuntimeError("Query failed")

        with (
            patch("idp.transformation.exporter.duckdb.connect", return_value=mock_duckdb),
            patch("idp.transformation.exporter.psycopg.connect", return_value=mock_pg),
            pytest.raises(RuntimeError, match="Query failed"),
        ):
            export_gold_to_postgres("test.duckdb", "gold")

        mock_duckdb.close.assert_called_once()
        mock_pg.close.assert_called_once()

    def test_export_uses_gold_schema(
        self, mock_env: None, sample_data: dict[str, pl.DataFrame]
    ) -> None:
        """Verify custom schema name is used."""
        mock_duckdb = MagicMock()
        mock_pg = MagicMock()
        mock_cursor = MagicMock()
        mock_pg.cursor.return_value.__enter__.return_value = mock_cursor

        mock_duckdb.execute.return_value.pl.side_effect = [
            sample_data["dim_countries"],
            sample_data["dim_indicators"],
            sample_data["dim_dates"],
            sample_data["fact_economic_indicators"],
        ]

        with (
            patch("idp.transformation.exporter.duckdb.connect", return_value=mock_duckdb),
            patch("idp.transformation.exporter.psycopg.connect", return_value=mock_pg),
        ):
            export_gold_to_postgres("test.duckdb", "custom_gold")

        # Check schema creation uses custom name
        create_schema_calls = [
            call
            for call in mock_cursor.execute.call_args_list
            if "CREATE SCHEMA" in str(call)
        ]
        for call_args in create_schema_calls:
            assert "custom_gold" in str(call_args)
            break
