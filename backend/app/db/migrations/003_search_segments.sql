-- Migration: 003_search_segments
-- Description: Create search segments, grid cells, clues, and POD tracking

-- Search segments (polygon areas assigned for searching)
CREATE TABLE search_segments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    search_type TEXT CHECK (search_type IN ('hasty', 'grid', 'line', 'attraction')),
    assigned_team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    -- Geometry
    polygon GEOMETRY(Polygon, 4326),
    area_sq_meters DOUBLE PRECISION,
    -- Grid configuration
    grid_spacing_meters DOUBLE PRECISION DEFAULT 10.0,
    -- POD tracking
    esw_meters DOUBLE PRECISION,
    coverage DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    pod DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    passes INTEGER NOT NULL DEFAULT 0,
    -- Status
    status TEXT NOT NULL DEFAULT 'unassigned' CHECK (
        status IN ('unassigned', 'assigned', 'in_progress', 'completed')
    ),
    priority INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_segments_incident ON search_segments (incident_id);
CREATE INDEX idx_segments_team ON search_segments (assigned_team_id);
CREATE INDEX idx_segments_spatial ON search_segments USING GIST (polygon);

-- Clues / evidence found during search
CREATE TABLE clues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    segment_id UUID REFERENCES search_segments(id) ON DELETE SET NULL,
    found_by_user_id UUID NOT NULL REFERENCES users(id),
    found_by_team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    -- Location
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    point GEOMETRY(Point, 4326),
    -- Details
    description TEXT NOT NULL,
    clue_type TEXT NOT NULL DEFAULT 'physical' CHECK (
        clue_type IN ('physical', 'track', 'scent', 'witness', 'other')
    ),
    photo_url TEXT,
    -- Metadata
    found_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_clues_incident ON clues (incident_id);
CREATE INDEX idx_clues_segment ON clues (segment_id);
CREATE INDEX idx_clues_spatial ON clues USING GIST (point);

INSERT INTO schema_migrations (version) VALUES ('003');
