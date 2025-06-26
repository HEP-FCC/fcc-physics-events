-- fcc-physics-events.sql
-- =============================================================================
--      PostgreSQL Schema for FCC Physics Data Model
-- =============================================================================

-- Step 1: Enable Necessary Extensions
-- ------------------------------------
-- pg_trgm is required for fuzzy string matching (trigram similarity)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Step 2: Define the Core Table Structure
-- -----------------------------------------

CREATE TABLE IF NOT EXISTS accelerator_types (
    accelerator_type_id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT (NOW() AT TIME ZONE 'utc')
);

COMMENT ON TABLE accelerator_types IS 'Stores types of accelerators (e.g., FCC-ee, FCC-hh)';

CREATE TABLE IF NOT EXISTS frameworks (
    framework_id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT (NOW() AT TIME ZONE 'utc')
);

COMMENT ON TABLE frameworks IS 'Stores simulation frameworks (e.g., Delphes, FullSim)';

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT (NOW() AT TIME ZONE 'utc'),
    UNIQUE (name)
);

COMMENT ON TABLE campaigns IS 'Stores campaign information representing code evolution cycles';

CREATE TABLE IF NOT EXISTS detectors (
    detector_id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    accelerator_type_id INTEGER REFERENCES accelerator_types(accelerator_type_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT (NOW() AT TIME ZONE 'utc')
);

COMMENT ON TABLE detectors IS 'Stores detector configurations';

-- Step 3: Create a Helper Function for JSONB search
-- -------------------------------------------------
-- This function concatenates all values of a JSONB object into a single string,
-- which can then be indexed for full-text search.
CREATE OR REPLACE FUNCTION jsonb_values_to_text(jsonb_in JSONB)
RETURNS TEXT LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    RETURN (SELECT string_agg(value, ' ') FROM jsonb_each_text(jsonb_in));
END;
$$;

COMMENT ON FUNCTION jsonb_values_to_text IS 'Extracts all text values from a JSONB object for searching.';

-- Main table for physics processes
CREATE TABLE IF NOT EXISTS processes (
    process_id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    accelerator_type_id INTEGER REFERENCES accelerator_types(accelerator_type_id) ON DELETE SET NULL,
    framework_id INTEGER REFERENCES frameworks(framework_id) ON DELETE SET NULL,
    campaign_id INTEGER REFERENCES campaigns(campaign_id) ON DELETE SET NULL,
    detector_id INTEGER REFERENCES detectors(detector_id) ON DELETE SET NULL,
    metadata JSONB,
    -- Generated column for efficient searching inside the metadata JSONB
    metadata_search_text TEXT GENERATED ALWAYS AS (jsonb_values_to_text(metadata)) STORED,
    created_at TIMESTAMPTZ DEFAULT (NOW() AT TIME ZONE 'utc')
);

COMMENT ON TABLE processes IS 'Stores individual processes with complete physics context';

-- Step 4: Create Indexes for Performance
-- ---------------------------------------

-- Standard B-tree indexes for foreign keys to speed up joins
CREATE INDEX IF NOT EXISTS idx_processes_accelerator_type_id ON processes(accelerator_type_id);
CREATE INDEX IF NOT EXISTS idx_processes_framework_id ON processes(framework_id);
CREATE INDEX IF NOT EXISTS idx_processes_campaign_id ON processes(campaign_id);
CREATE INDEX IF NOT EXISTS idx_processes_detector_id ON processes(detector_id);

-- GIN (Generalized Inverted Index) with trigram operations for fast fuzzy search and ILIKE/regex
CREATE INDEX IF NOT EXISTS processes_metadata_search_gin_idx ON processes USING GIN (metadata_search_text gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_processes_name_gin ON processes USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_detectors_name_gin ON detectors USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_campaigns_name_gin ON campaigns USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_frameworks_name_gin ON frameworks USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_accelerator_types_name_gin ON accelerator_types USING GIN (name gin_trgm_ops);


-- Step 5: Add Software Stacks Table
-- -----------------------------------------

CREATE TABLE IF NOT EXISTS stacks (
    stack_id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    version VARCHAR(255),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT (NOW() AT TIME ZONE 'utc')
);

COMMENT ON TABLE stacks IS 'Stores software stack configurations with paths to setup scripts';

-- Create indexes for the stacks table
CREATE INDEX IF NOT EXISTS idx_stacks_name_gin ON stacks USING GIN (name gin_trgm_ops);
