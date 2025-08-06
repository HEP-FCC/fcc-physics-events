-- Extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- for fuzzy string matching (trigram similarity)

-- Helper functions
-- This function concatenates all values of a JSONB object into a single string,
-- which can then be indexed for full-text search.
CREATE OR REPLACE FUNCTION jsonb_values_to_text(jsonb_in JSONB)
RETURNS TEXT LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    RETURN (SELECT string_agg(value, ' ') FROM jsonb_each_text(jsonb_in));
END;
$$;

-- Tables
CREATE TABLE IF NOT EXISTS accelerators (
    accelerator_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stages (
    stage_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS detectors (
    detector_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    accelerator_id INTEGER REFERENCES accelerators(accelerator_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS software_stacks (
    software_stack_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS datasets (
    dataset_id BIGSERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    -- # TODO: ON DELETE SET NULL will leave orphaned dataset records if a referenced entity is deleted.
    -- Consider if ON DELETE RESTRICT or making the column NOT NULL would be more appropriate.
    accelerator_id INTEGER REFERENCES accelerators(accelerator_id) ON DELETE SET NULL,
    stage_id INTEGER REFERENCES stages(stage_id) ON DELETE SET NULL,
    campaign_id INTEGER REFERENCES campaigns(campaign_id) ON DELETE SET NULL,
    detector_id INTEGER REFERENCES detectors(detector_id) ON DELETE SET NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_edited_at TIMESTAMPTZ DEFAULT NULL,
    edited_by_name TEXT DEFAULT NULL
);


-- Indexes
-- Standard B-tree indexes for foreign keys to speed up joins
CREATE INDEX IF NOT EXISTS idx_datasets_accelerator_id ON datasets(accelerator_id);
CREATE INDEX IF NOT EXISTS idx_datasets_stage_id ON datasets(stage_id);
CREATE INDEX IF NOT EXISTS idx_datasets_campaign_id ON datasets(campaign_id);
CREATE INDEX IF NOT EXISTS idx_datasets_detector_id ON datasets(detector_id);

-- GIN (Generalized Inverted Index) with trigram operations for fast fuzzy search and ILIKE/regex
CREATE INDEX IF NOT EXISTS idx_detectors_name_gin ON detectors USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_campaigns_name_gin ON campaigns USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_stages_name_gin ON stages USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_accelerators_name_gin ON accelerators USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_stacks_name_gin ON software_stacks USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_datasets_name_gin ON datasets USING GIN (name gin_trgm_ops);

-- GIN index on an expression to enable fast fuzzy search on JSONB values
CREATE INDEX IF NOT EXISTS datasets_metadata_search_gin_idx ON datasets USING GIN (jsonb_values_to_text(metadata) gin_trgm_ops);
