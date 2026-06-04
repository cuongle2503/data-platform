WITH source AS (
    SELECT * FROM read_parquet('s3://bronze/world_bank/indicators/*.parquet')
),

cleaned AS (
    SELECT
        UPPER(TRIM(country_code)) AS country_code,
        TRIM(country_name) AS country_name,
        UPPER(TRIM(indicator_code)) AS indicator_code,
        TRIM(indicator_name) AS indicator_name,
        CAST(year AS INTEGER) AS year,
        CAST(value AS DOUBLE) AS value,
        TRIM(source) AS source,
        ingested_at,
        ROW_NUMBER() OVER (
            PARTITION BY country_code, indicator_code, year
            ORDER BY ingested_at DESC
        ) AS rn
    FROM source
)

SELECT
    country_code,
    country_name,
    indicator_code,
    indicator_name,
    year,
    value,
    source
FROM cleaned
WHERE rn = 1
