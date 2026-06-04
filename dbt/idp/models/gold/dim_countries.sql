WITH source AS (
    SELECT * FROM {{ ref('seed_countries') }}
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['country_code']) }} AS country_key,
    country_code,
    country_name,
    region,
    income_group,
    CAST(is_asean AS BOOLEAN) AS is_asean,
    CAST(is_primary AS BOOLEAN) AS is_primary
FROM source
