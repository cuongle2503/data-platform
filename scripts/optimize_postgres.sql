-- Optimize Gold Schema

-- Add UNIQUE constraints for the surrogate keys if not existing
ALTER TABLE gold.dim_countries DROP CONSTRAINT IF EXISTS uq_dim_countries_key;
ALTER TABLE gold.dim_countries ADD CONSTRAINT uq_dim_countries_key UNIQUE (country_key);

ALTER TABLE gold.dim_indicators DROP CONSTRAINT IF EXISTS uq_dim_indicators_key;
ALTER TABLE gold.dim_indicators ADD CONSTRAINT uq_dim_indicators_key UNIQUE (indicator_key);

-- Add foreign key constraints to fact table
ALTER TABLE gold.fact_economic_indicators DROP CONSTRAINT IF EXISTS fk_country;
ALTER TABLE gold.fact_economic_indicators
    ADD CONSTRAINT fk_country FOREIGN KEY (country_key) REFERENCES gold.dim_countries(country_key);

ALTER TABLE gold.fact_economic_indicators DROP CONSTRAINT IF EXISTS fk_indicator;
ALTER TABLE gold.fact_economic_indicators
    ADD CONSTRAINT fk_indicator FOREIGN KEY (indicator_key) REFERENCES gold.dim_indicators(indicator_key);

-- Composite index for the main query pattern
DROP INDEX IF EXISTS gold.idx_fact_economic_indicators_query;
CREATE INDEX idx_fact_economic_indicators_query
    ON gold.fact_economic_indicators(indicator_key, country_key, date_key, source);

-- View for latest values
CREATE OR REPLACE VIEW gold.v_latest_indicators AS
WITH ranked AS (
    SELECT
        indicator_key,
        country_key,
        date_key,
        value,
        source,
        ROW_NUMBER() OVER(PARTITION BY indicator_key, country_key ORDER BY date_key DESC) as rn
    FROM gold.fact_economic_indicators
)
SELECT indicator_key, country_key, date_key, value, source
FROM ranked
WHERE rn = 1;
