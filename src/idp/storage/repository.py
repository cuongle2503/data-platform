"""PostgreSQL storage repository for countries, indicators, and timeseries data."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class StorageRepository:
    """Repository layer for the Gold and Embeddings databases."""

    def __init__(self, conn: Any) -> None:
        self.conn = conn

    def get_countries(self) -> list[dict[str, Any]]:
        """Get all countries, ordered by country_code."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT country_code, country_name, region, income_group, is_asean, is_primary
            FROM gold.dim_countries
            ORDER BY country_code
        """)
        rows = cur.fetchall()
        return [
            {
                "country_code": r[0],
                "country_name": r[1],
                "region": r[2],
                "income_group": r[3],
                "is_asean": r[4],
                "is_primary": r[5],
            }
            for r in rows
        ]

    def get_country(self, code: str) -> dict[str, Any] | None:
        """Get a single country by code."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT country_code, country_name, region, income_group, is_asean, is_primary "
            "FROM gold.dim_countries WHERE country_code = %s",
            (code,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "country_code": row[0],
            "country_name": row[1],
            "region": row[2],
            "income_group": row[3],
            "is_asean": row[4],
            "is_primary": row[5],
        }

    def get_indicators(self) -> list[dict[str, Any]]:
        """Get all indicators, ordered by indicator_code."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT indicator_code, indicator_name, category, unit, description
            FROM gold.dim_indicators
            ORDER BY indicator_code
        """)
        rows = cur.fetchall()
        return [
            {
                "indicator_code": r[0],
                "indicator_name": r[1],
                "category": r[2],
                "unit": r[3],
                "description": r[4],
            }
            for r in rows
        ]

    def get_indicator(self, code: str) -> dict[str, Any] | None:
        """Get a single indicator by code."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT indicator_code, indicator_name, category, unit, description "
            "FROM gold.dim_indicators WHERE indicator_code = %s",
            (code,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "indicator_code": row[0],
            "indicator_name": row[1],
            "category": row[2],
            "unit": row[3],
            "description": row[4],
        }

    def get_timeseries(
        self,
        country: str,
        indicators: list[str],
        years: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Get time series data for a country and list of indicators, optionally filtered by years."""
        cur = self.conn.cursor()
        query = """
            SELECT
                dc.country_code,
                di.indicator_code,
                dd.year,
                f.value,
                f.source
            FROM gold.fact_economic_indicators f
            JOIN gold.dim_countries dc ON f.country_key = dc.country_key
            JOIN gold.dim_indicators di ON f.indicator_key = di.indicator_key
            JOIN gold.dim_dates dd ON f.date_key = dd.date_key
            WHERE dc.country_code = %s
              AND di.indicator_code = ANY(%s)
        """
        params: list[Any] = [country, indicators]

        if years:
            query += " AND dd.year = ANY(%s)"
            params.append(years)

        query += " ORDER BY di.indicator_code, dd.year"

        cur.execute(query, params)
        rows = cur.fetchall()
        return [
            {
                "country_code": r[0],
                "indicator_code": r[1],
                "year": r[2],
                "value": r[3],
                "source": r[4],
            }
            for r in rows
        ]

    def search_indicators_lexical(self, query: str) -> list[dict[str, Any]]:
        """Full-text search against indicator name and description."""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT indicator_code, indicator_name, description, category
            FROM gold.dim_indicators
            WHERE indicator_name ILIKE %s
               OR description ILIKE %s
            ORDER BY indicator_code
            LIMIT 50
            """,
            (f"%{query}%", f"%{query}%"),
        )
        rows = cur.fetchall()
        return [
            {"indicator_code": r[0], "indicator_name": r[1], "description": r[2], "category": r[3]}
            for r in rows
        ]

    def search_indicators_semantic(
        self,
        query_embedding: list[float],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search indicators by semantic similarity using pgvector."""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                di.indicator_code,
                di.indicator_name,
                di.category,
                1 - (ee.embedding <=> %s::vector) AS similarity
            FROM embeddings.economic_embeddings ee
            JOIN gold.dim_indicators di ON ee.ref_id = di.indicator_code
            WHERE ee.ref_type = 'economic_indicator'
            ORDER BY ee.embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, limit),
        )
        rows = cur.fetchall()
        return [
            {"indicator_code": r[0], "indicator_name": r[1], "category": r[2], "similarity": r[3]}
            for r in rows
        ]
