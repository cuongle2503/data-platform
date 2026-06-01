WITH staging AS (
    SELECT * FROM {{ ref('stg_world_bank__indicators') }}
),

countries AS (
    SELECT * FROM {{ ref('dim_countries') }}
),

indicators AS (
    SELECT * FROM {{ ref('dim_indicators') }}
),

dates AS (
    SELECT * FROM {{ ref('dim_dates') }}
)

SELECT
    indicators.indicator_key,
    countries.country_key,
    dates.date_key,
    staging.value,
    staging.source,
    CURRENT_TIMESTAMP AS loaded_at
FROM staging
INNER JOIN countries
    ON staging.country_code = countries.country_code
INNER JOIN indicators
    ON staging.indicator_code = indicators.indicator_code
INNER JOIN dates
    ON staging.year = dates.year
