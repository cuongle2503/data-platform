-- Create embeddings schema for pgvector

CREATE SCHEMA IF NOT EXISTS embeddings;

CREATE TABLE IF NOT EXISTS embeddings.economic_embeddings (
    id SERIAL PRIMARY KEY,
    ref_type VARCHAR(50) NOT NULL,
    ref_id VARCHAR(255) NOT NULL,
    embedding VECTOR(768) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ref_type, ref_id)
);

-- Create HNSW index for fast vector similarity search
CREATE INDEX IF NOT EXISTS idx_economic_embeddings_hnsw 
    ON embeddings.economic_embeddings 
    USING hnsw (embedding vector_cosine_ops);

-- Create index on ref_type for filtering
CREATE INDEX IF NOT EXISTS idx_economic_embeddings_ref_type 
    ON embeddings.economic_embeddings(ref_type);
