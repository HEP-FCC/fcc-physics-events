-- Populate Accelerator Types
INSERT INTO accelerator_types (name, description) VALUES
('FCC-ee', 'Future Circular Collider - electron-positron option'),
('FCC-hh', 'Future Circular Collider - hadron-hadron option');

-- Populate Frameworks
INSERT INTO frameworks (name, description) VALUES
('Delphes', 'Fast detector simulation framework with parameterized detector response'),
('FullSim', 'Full detector simulation with detailed particle interactions');

-- Populate Campaigns
INSERT INTO campaigns (name, description) VALUES
('Spring2023', 'First production campaign with revised detector geometries'),
('Summer2023', 'Updated magnetic field maps and improved tracking algorithms'),
('Winter2024', 'Enhanced calorimeter response and energy calibration'),
('Spring2024', 'Integration of new jet clustering algorithms'),
('Summer2024', 'Improved particle identification and flavor tagging');

-- Populate Detectors
INSERT INTO detectors (name, accelerator_type_id) VALUES
('CLD', 1), -- CLIC-Like Detector for FCC-ee
('IDEA', 1), -- Innovative Detector for Electron-positron Accelerator for FCC-ee
('FCC-hh Baseline', 2), -- Baseline detector for FCC-hh
('FCC-hh Forward', 2); -- Forward detector option for FCC-hh

-- Populate Samples (100 entries)
-- Using a loop to generate varied sample data
DO $$
DECLARE
    process_types TEXT[] := ARRAY['Higgs_ZZ', 'Higgs_WW', 'Higgs_bb', 'Higgs_cc', 'Higgs_gg', 'ZZ_4l', 'WW_lnu', 'Z_ll', 'ttbar', 'dijet'];
    energies NUMERIC[] := ARRAY[91.2, 160, 240, 365, 500, 13000, 14000, 27000, 100000];
    sample_counter INTEGER := 1;
    acc_type_id INTEGER;
    frame_id INTEGER;
    camp_id INTEGER;
    det_id INTEGER;
    process_idx INTEGER;
    energy_idx INTEGER;
    events INTEGER;
    cross_section NUMERIC;
BEGIN
    -- Create 100 sample entries
    FOR i IN 1..100 LOOP
        -- Determine parameters for this sample
        acc_type_id := 1 + (i % 2); -- Alternating between 1 and 2
        frame_id := 1 + (i % 2); -- Alternating between 1 and 2
        camp_id := 1 + (i % 5); -- Rotating through 1 to 5

        -- Detector depends on accelerator type
        IF acc_type_id = 1 THEN -- FCC-ee
            det_id := 1 + (i % 2); -- CLD or IDEA
        ELSE -- FCC-hh
            det_id := 3 + (i % 2); -- FCC-hh Baseline or Forward
        END IF;

        process_idx := 1 + (i % array_length(process_types, 1));

        -- Energy selection depends on accelerator
        IF acc_type_id = 1 THEN -- FCC-ee
            energy_idx := 1 + (i % 5); -- First 5 energies (91.2 to 500 GeV)
        ELSE -- FCC-hh
            energy_idx := 6 + (i % 4); -- Last 4 energies (13 to 100 TeV)
        END IF;

        events := (random() * 900000 + 100000)::INTEGER; -- Between 100k and 1M events
        cross_section := random() * 100; -- Random cross-section up to 100 pb

        -- Insert the sample
        INSERT INTO samples (
            name,
            accelerator_type_id,
            framework_id,
            campaign_id,
            detector_id,
            metadata
        ) VALUES (
            process_types[process_idx] || '_' || energies[energy_idx] || '_sample' || i,
            acc_type_id,
            frame_id,
            camp_id,
            det_id,
            jsonb_build_object(
                'process', process_types[process_idx],
                'energy', energies[energy_idx],
                'cross_section', cross_section,
                'events', events,
                'generator', CASE WHEN i % 3 = 0 THEN 'Pythia' WHEN i % 3 = 1 THEN 'MadGraph' ELSE 'Sherpa' END,
                'luminosity', events / cross_section,
                'additional_cuts', jsonb_build_object(
                    'pt_min', (random() * 20 + 5)::NUMERIC(5,2),
                    'eta_max', (random() * 2 + 2)::NUMERIC(3,1),
                    'isolation', (random() * 0.3 + 0.1)::NUMERIC(3,2)
                )
            )
        );
    END LOOP;
END $$;

-- Confirm data was inserted successfully
SELECT COUNT(*) AS accelerator_types_count FROM accelerator_types;
SELECT COUNT(*) AS frameworks_count FROM frameworks;
SELECT COUNT(*) AS campaigns_count FROM campaigns;
SELECT COUNT(*) AS detectors_count FROM detectors;
SELECT COUNT(*) AS samples_count FROM samples;
