-- Aquaculture Intelligence System (AIS)
-- Database Migration 001: Initial Hypertables & Relational Schema Setup

CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. sensor_readings: TimescaleDB hypertable for continuous IoT sensor streams
CREATE TABLE IF NOT EXISTS sensor_readings (
    pond_id UUID NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    do_mgl DOUBLE PRECISION,
    ph DOUBLE PRECISION,
    temp_c DOUBLE PRECISION,
    nh3_mgl DOUBLE PRECISION,
    turbidity DOUBLE PRECISION,
    data_quality VARCHAR(20) DEFAULT 'VALID' CHECK (data_quality IN ('VALID', 'IMPAIRED', 'INVALID'))
);

SELECT create_hypertable('sensor_readings', 'ts', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_pond_ts ON sensor_readings (pond_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_ts_brin ON sensor_readings USING brin (ts);

-- 2. disease_events: Relational table for disease diagnostic events
CREATE TABLE IF NOT EXISTS disease_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pond_id UUID NOT NULL,
    image_path TEXT NOT NULL,
    disease_class VARCHAR(50) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('Mild', 'Moderate', 'Severe', 'Critical')),
    treatment_id INT,
    model_version VARCHAR(30) NOT NULL,
    ts TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_disease_events_pond_ts ON disease_events (pond_id, ts DESC);

-- 3. pond_cycles: Farm stocking and cycle management
CREATE TABLE IF NOT EXISTS pond_cycles (
    cycle_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pond_id UUID NOT NULL,
    species VARCHAR(50) NOT NULL,
    stocking_date DATE NOT NULL,
    n_fish INT NOT NULL,
    stocking_weight_g DOUBLE PRECISION NOT NULL,
    target_weight_g DOUBLE PRECISION NOT NULL,
    harvest_date DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'HARVESTED', 'ABORTED'))
);

-- 4. feed_logs: Daily feed recommendation & actual log tracking
CREATE TABLE IF NOT EXISTS feed_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pond_id UUID NOT NULL,
    ts TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    feed_kg DOUBLE PRECISION NOT NULL,
    feed_type VARCHAR(50),
    protein_pct DOUBLE PRECISION,
    fcr_actual DOUBLE PRECISION
);

-- 5. rag_chunks: Vector database store for RAG aquaculture knowledge base
CREATE TABLE IF NOT EXISTS rag_chunks (
    chunk_id SERIAL PRIMARY KEY,
    doc_source VARCHAR(255) NOT NULL,
    section TEXT,
    page_num INT,
    content TEXT NOT NULL,
    embedding vector(384) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_hnsw ON rag_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- 6. prediction_logs: MLOps model drift tracking
CREATE TABLE IF NOT EXISTS prediction_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(30) NOT NULL,
    input_hash VARCHAR(64),
    prediction JSONB NOT NULL,
    confidence DOUBLE PRECISION,
    latency_ms INT NOT NULL,
    ts TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
