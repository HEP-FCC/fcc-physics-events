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

CREATE TABLE IF NOT EXISTS file_types (
    file_type_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS datasets (
    dataset_id BIGSERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    -- Foreign key relationships with proper constraints
    accelerator_id INTEGER REFERENCES accelerators(accelerator_id) ON DELETE SET NULL,
    stage_id INTEGER REFERENCES stages(stage_id) ON DELETE SET NULL,
    campaign_id INTEGER REFERENCES campaigns(campaign_id) ON DELETE SET NULL,
    detector_id INTEGER REFERENCES detectors(detector_id) ON DELETE SET NULL,
    file_type_id INTEGER REFERENCES file_types(file_type_id) ON DELETE SET NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_edited_at TIMESTAMPTZ DEFAULT NULL,
    edited_by_name TEXT DEFAULT NULL,

    -- Add constraints for data integrity
    CONSTRAINT chk_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT chk_edited_at_after_created CHECK (last_edited_at IS NULL OR last_edited_at >= created_at),
    CONSTRAINT chk_metadata_valid CHECK (metadata IS NULL OR jsonb_typeof(metadata) = 'object')
);

-- Indexes
-- Standard B-tree indexes for foreign keys to speed up joins
CREATE INDEX IF NOT EXISTS idx_datasets_accelerator_id ON datasets(accelerator_id);
CREATE INDEX IF NOT EXISTS idx_datasets_stage_id ON datasets(stage_id);
CREATE INDEX IF NOT EXISTS idx_datasets_campaign_id ON datasets(campaign_id);
CREATE INDEX IF NOT EXISTS idx_datasets_detector_id ON datasets(detector_id);
CREATE INDEX IF NOT EXISTS idx_datasets_file_type_id ON datasets(file_type_id);

-- GIN (Generalized Inverted Index) with trigram operations for fast fuzzy search and ILIKE/regex
CREATE INDEX IF NOT EXISTS idx_accelerators_name_gin ON accelerators USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_stages_name_gin ON stages USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_campaigns_name_gin ON campaigns USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_detectors_name_gin ON detectors USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_file_types_name_gin ON file_types USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_datasets_name_gin ON datasets USING GIN (name gin_trgm_ops);

-- GIN index on an expression to enable fast fuzzy search on JSONB values
CREATE INDEX IF NOT EXISTS idx_datasets_metadata_search_gin ON datasets USING GIN (jsonb_values_to_text(metadata) gin_trgm_ops);

-- Additional JSONB indexes for metadata search optimization
-- Full JSONB index for containment queries (e.g., searching for specific key-value pairs)
CREATE INDEX IF NOT EXISTS idx_datasets_metadata_gin ON datasets USING GIN (metadata);

-- Optimized JSONB index for path-based queries (smaller, faster for specific patterns)
CREATE INDEX IF NOT EXISTS idx_datasets_metadata_path_gin ON datasets USING GIN (metadata jsonb_path_ops);

-- Specific indexes for commonly searched metadata fields (based on your JSON structure)
-- These will be much faster for queries targeting specific metadata fields
CREATE INDEX IF NOT EXISTS idx_datasets_metadata_process_name ON datasets USING GIN ((metadata->>'process-name') gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_datasets_metadata_description ON datasets USING GIN ((metadata->>'description') gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_datasets_metadata_comment ON datasets USING GIN ((metadata->>'comment') gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_datasets_metadata_status ON datasets USING BTREE ((metadata->>'status'));
CREATE INDEX IF NOT EXISTS idx_datasets_metadata_accelerator ON datasets USING BTREE ((metadata->>'accelerator'));
CREATE INDEX IF NOT EXISTS idx_datasets_metadata_detector ON datasets USING BTREE ((metadata->>'detector'));
CREATE INDEX IF NOT EXISTS idx_datasets_metadata_campaign ON datasets USING BTREE ((metadata->>'campaign'));

-- Temporal indexes for sorting and filtering by timestamps
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON datasets(created_at);
CREATE INDEX IF NOT EXISTS idx_datasets_last_edited_at ON datasets(last_edited_at);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at_desc ON datasets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_datasets_last_edited_at_desc ON datasets(last_edited_at DESC);

-- Composite indexes for common query patterns
-- This supports pagination and sorting by last_edited_at which is common in your app
CREATE INDEX IF NOT EXISTS idx_datasets_edited_id_composite ON datasets(last_edited_at DESC, dataset_id);

-- Index for efficient counting and existence checks
CREATE INDEX IF NOT EXISTS idx_datasets_name_lower ON datasets(LOWER(name));

-- Partial indexes for active/completed datasets (if status filtering is common)
CREATE INDEX IF NOT EXISTS idx_datasets_status_done ON datasets(dataset_id)
WHERE metadata->>'status' = 'done';

-- Partial index for datasets with metadata (excludes NULL metadata)
CREATE INDEX IF NOT EXISTS idx_datasets_with_metadata ON datasets(dataset_id)
WHERE metadata IS NOT NULL;

-- Performance optimization: Set statistics targets for better query planning
-- Increase statistics for frequently queried columns
ALTER TABLE datasets ALTER COLUMN name SET STATISTICS 1000;
ALTER TABLE datasets ALTER COLUMN metadata SET STATISTICS 1000;
ALTER TABLE datasets ALTER COLUMN last_edited_at SET STATISTICS 500;

-- Set statistics for lookup tables
ALTER TABLE accelerators ALTER COLUMN name SET STATISTICS 100;
ALTER TABLE stages ALTER COLUMN name SET STATISTICS 100;
ALTER TABLE campaigns ALTER COLUMN name SET STATISTICS 100;
ALTER TABLE detectors ALTER COLUMN name SET STATISTICS 100;
ALTER TABLE file_types ALTER COLUMN name SET STATISTICS 100;
