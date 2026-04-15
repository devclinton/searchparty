-- Migration: 005_trails
-- Description: Known trails, custom routes, and trail junctions

CREATE TABLE trails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    name TEXT,
    trail_type TEXT NOT NULL DEFAULT 'path' CHECK (trail_type IN (
        'path', 'footway', 'track', 'bridleway', 'cycleway', 'road', 'custom'
    )),
    source TEXT NOT NULL DEFAULT 'custom' CHECK (source IN (
        'osm', 'usfs', 'nps', 'blm', 'state', 'shapefile', 'custom'
    )),
    source_id TEXT,
    -- Attributes
    surface TEXT,
    difficulty TEXT,
    -- Geometry
    geometry GEOMETRY(LineString, 4326) NOT NULL,
    length_meters DOUBLE PRECISION,
    -- Metadata
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_trails_incident ON trails (incident_id);
CREATE INDEX idx_trails_spatial ON trails USING GIST (geometry);
CREATE INDEX idx_trails_source ON trails (source, source_id);

-- Trail junctions (intersection points detected from trail network)
CREATE TABLE trail_junctions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    point GEOMETRY(Point, 4326) NOT NULL,
    trail_count INTEGER NOT NULL DEFAULT 2,
    trail_names TEXT[],
    priority_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_junctions_incident ON trail_junctions (incident_id);
CREATE INDEX idx_junctions_spatial ON trail_junctions USING GIST (point);

INSERT INTO schema_migrations (version) VALUES ('005');
