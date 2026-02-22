-- ============================================================
-- JobMatcher Database Schema
-- PostgreSQL 16 + pgvector
-- ============================================================

-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- Jobs table: ข้อมูลงานหลัก
-- ============================================================
CREATE TABLE IF NOT EXISTS jobs (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    company         TEXT,
    location        TEXT,
    salary          TEXT,
    link            TEXT UNIQUE NOT NULL,
    description     TEXT,
    skills          JSONB,              -- ["Python", "SQL", "Airflow"]
    experience_years TEXT,               -- "3-5 years"
    job_type        TEXT,                -- "Full-time", "Contract", "Internship"
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Job Embeddings table: vector สำหรับ semantic search
-- ============================================================
CREATE TABLE IF NOT EXISTS job_embeddings (
    id          SERIAL PRIMARY KEY,
    job_id      INTEGER UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
    embedding   vector(768),            -- nomic-embed-text = 768 dimensions
    model       TEXT DEFAULT 'gemini-embedding-001',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Indexes
-- ============================================================
-- Vector similarity search index (IVFFlat)
-- หมายเหตุ: IVFFlat ต้อง build หลัง INSERT ข้อมูลแล้ว จึงใช้ HNSW แทนตอนนี้
CREATE INDEX IF NOT EXISTS idx_job_embeddings_hnsw
ON job_embeddings USING hnsw (embedding vector_cosine_ops);

-- Full-text search on title
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs USING gin(to_tsvector('english', title));

-- Skills lookup
CREATE INDEX IF NOT EXISTS idx_jobs_skills ON jobs USING gin(skills);

-- Link uniqueness (already via UNIQUE constraint)

-- ============================================================
-- Auto-update updated_at timestamp
-- ============================================================
-- 1. สร้าง Function สำหรับอัปเดตเวลา
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 2. นำ Function ไปผูกกับตาราง jobs
CREATE TRIGGER update_jobs_modtime
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();