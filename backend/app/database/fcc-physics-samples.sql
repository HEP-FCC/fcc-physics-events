-- fcc-physics-samples.sql
-- =============================================================================
--      PostgreSQL Schema for Unified Detector & Campaign Metadata Database
-- =============================================================================

-- Step 1: Enable Necessary Extensions
-- ------------------------------------
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Step 2: Define the Core Table Structure
-- -----------------------------------------

CREATE TABLE IF NOT EXISTS detectors (
    detector_id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE detectors IS 'Stores the main detector systems.';

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    detector_id INTEGER NOT NULL REFERENCES detectors(detector_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (detector_id, name)
);

COMMENT ON TABLE campaigns IS 'Stores campaign information, each linked to a specific detector.';

-- Step 3: Create a Helper Function for JSONB search
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION jsonb_values_to_text(jsonb_in JSONB)
RETURNS TEXT LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    RETURN (SELECT string_agg(value, ' ') FROM jsonb_each_text(jsonb_in));
END;
$$;

COMMENT ON FUNCTION jsonb_values_to_text IS 'Extracts all text values from a JSONB object for searching.';

CREATE TABLE IF NOT EXISTS samples (
    sample_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    metadata JSONB,
    metadata_search_text TEXT GENERATED ALWAYS AS (jsonb_values_to_text(metadata)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE samples IS 'Stores individual samples, linked to a campaign.';

-- Step 4: Create Indexes for Performance
-- ---------------------------------------
CREATE INDEX IF NOT EXISTS idx_campaigns_detector_id ON campaigns(detector_id);
CREATE INDEX IF NOT EXISTS idx_samples_campaign_id ON samples(campaign_id);
CREATE INDEX IF NOT EXISTS samples_metadata_search_gin_idx ON samples USING GIN (metadata_search_text gin_trgm_ops);
