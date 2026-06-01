WITH source AS (
    SELECT * FROM {{ ref('seed_indicators') }}
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['indicator_code']) }} AS indicator_key,
    indicator_code,
    indicator_name,
    source_system,
    category,
    unit,
    frequency,
    description
FROM source
