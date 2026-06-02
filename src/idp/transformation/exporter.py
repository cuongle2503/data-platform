"""Export Gold tables from DuckDB to PostgreSQL."""

import logging

import duckdb
import polars as pl
import psycopg
import typer
from psycopg import sql

from idp.common.config import get_settings

logger = logging.getLogger(__name__)

app = typer.Typer()

GOLD_TABLES = [
    "dim_countries",
    "dim_indicators",
    "dim_dates",
    "fact_economic_indicators",
]


def export_gold_to_postgres(
    duckdb_path: str = "data/gold.duckdb",
    schema_name: str = "gold",
) -> dict[str, int]:
    """Export all Gold tables from DuckDB to PostgreSQL.

    Args:
        duckdb_path: Path to DuckDB database file
        schema_name: PostgreSQL schema name to create/use

    Returns:
        Dictionary mapping table names to row counts exported
    """
    settings = get_settings()
    db_url = settings.postgres.database_url

    logger.info(f"Connecting to DuckDB at {duckdb_path}")
    duckdb_conn = duckdb.connect(duckdb_path, read_only=True)

    logger.info(f"Connecting to PostgreSQL at {settings.postgres.host}")
    pg_conn = psycopg.connect(db_url)

    row_counts: dict[str, int] = {}

    try:
        # Create schema if not exists
        with pg_conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema_name))
            )
            pg_conn.commit()
            logger.info(f"Schema '{schema_name}' ready")

        # Export each table
        for table_name in GOLD_TABLES:
            logger.info(f"Exporting {table_name}...")

            # Read from DuckDB
            df = duckdb_conn.execute(f"SELECT * FROM {table_name}").pl()
            row_count = len(df)

            if row_count == 0:
                logger.warning(f"Table {table_name} is empty, skipping")
                row_counts[table_name] = 0
                continue

            # Create table in PostgreSQL with matching schema
            qualified_table = f"{schema_name}.{table_name}"

            with pg_conn.cursor() as cur:
                # Drop and recreate table
                cur.execute(
                    sql.SQL("DROP TABLE IF EXISTS {}.{} CASCADE").format(
                        sql.Identifier(schema_name), sql.Identifier(table_name)
                    )
                )

                # Infer PostgreSQL types from Polars
                create_cols = []
                for col_name, dtype in zip(df.columns, df.dtypes):
                    pg_type = _polars_to_postgres_type(dtype)
                    create_cols.append(f"{col_name} {pg_type}")

                create_sql = f"CREATE TABLE {qualified_table} ({', '.join(create_cols)})"
                cur.execute(create_sql)
                pg_conn.commit()
                logger.info(f"Created table {qualified_table}")

                # Bulk insert using COPY
                with cur.copy(
                    f"COPY {qualified_table} ({', '.join(df.columns)}) FROM STDIN"
                ) as copy:
                    for row in df.iter_rows():
                        copy.write_row(row)

                pg_conn.commit()
                logger.info(f"Inserted {row_count} rows into {qualified_table}")
                row_counts[table_name] = row_count

    finally:
        duckdb_conn.close()
        pg_conn.close()

    return row_counts


def _polars_to_postgres_type(dtype: pl.DataType) -> str:
    """Map Polars data type to PostgreSQL type.

    Args:
        dtype: Polars data type

    Returns:
        PostgreSQL type string
    """
    if dtype == pl.Int32 or dtype == pl.Int64:
        return "BIGINT"
    elif dtype == pl.Float64:
        return "DOUBLE PRECISION"
    elif dtype == pl.Boolean:
        return "BOOLEAN"
    elif dtype == pl.Datetime:
        return "TIMESTAMP"
    elif dtype == pl.Date:
        return "DATE"
    elif dtype == pl.Utf8:
        return "TEXT"
    else:
        return "TEXT"


@app.command()
def main(
    duckdb_path: str = typer.Option("data/gold.duckdb", help="Path to DuckDB database file"),
    schema_name: str = typer.Option("gold", help="PostgreSQL schema name"),
) -> None:
    """Export Gold tables from DuckDB to PostgreSQL."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting DuckDB → PostgreSQL export")
    row_counts = export_gold_to_postgres(duckdb_path, schema_name)

    logger.info("Export complete!")
    for table, count in row_counts.items():
        logger.info(f"  {table}: {count} rows")


if __name__ == "__main__":
    app()
