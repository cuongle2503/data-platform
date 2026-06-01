WITH years AS (
    SELECT UNNEST(generate_series(1950, 2030)) AS year
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['year']) }} AS date_key,
    year,
    (year // 10) * 10 AS decade,
    CASE
        WHEN year < 2000 THEN 20
        ELSE 21
    END AS century
FROM years
