-- Runs automatically on first container init (docker-entrypoint-initdb.d).
-- Ensures the pgvector extension is ready before Phase 2 adds
-- regulation_chunk.embedding (vector) columns.
CREATE EXTENSION IF NOT EXISTS vector;
