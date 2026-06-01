-- Initialize PostgreSQL database for IDP
-- This script runs automatically on first container startup

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schemas for Medallion architecture
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS embeddings;

-- Grant permissions to idp_user
GRANT ALL PRIVILEGES ON SCHEMA bronze TO idp_user;
GRANT ALL PRIVILEGES ON SCHEMA silver TO idp_user;
GRANT ALL PRIVILEGES ON SCHEMA gold TO idp_user;
GRANT ALL PRIVILEGES ON SCHEMA embeddings TO idp_user;

-- Create Airflow database (if not exists)
SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec
