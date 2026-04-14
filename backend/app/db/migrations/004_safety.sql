-- Migration: 004_safety
-- Description: Hazard zones, emergency alerts, safety briefings

-- Hazard zones
CREATE TABLE hazard_zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    hazard_type TEXT NOT NULL CHECK (hazard_type IN (
        'cliff', 'mine_shaft', 'avalanche', 'flood',
        'water', 'wildlife', 'unstable_ground', 'other'
    )),
    severity TEXT NOT NULL DEFAULT 'warning' CHECK (severity IN ('caution', 'warning', 'danger')),
    description TEXT,
    -- Geometry: polygon for area hazards, point+radius for spot hazards
    polygon GEOMETRY(Polygon, 4326),
    center_lat DOUBLE PRECISION,
    center_lon DOUBLE PRECISION,
    radius_meters DOUBLE PRECISION DEFAULT 100.0,
    -- Geofence alert buffer in meters beyond the hazard boundary
    alert_buffer_meters DOUBLE PRECISION NOT NULL DEFAULT 200.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_hazard_zones_incident ON hazard_zones (incident_id);
CREATE INDEX idx_hazard_zones_spatial ON hazard_zones USING GIST (polygon);

-- Emergency distress signals
CREATE TABLE emergency_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    point GEOMETRY(Point, 4326),
    message TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_emergency_alerts_incident ON emergency_alerts (incident_id);
CREATE INDEX idx_emergency_alerts_status ON emergency_alerts (status);

-- Safety briefing checklists
CREATE TABLE safety_briefings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    briefed_by_user_id UUID NOT NULL REFERENCES users(id),
    items JSONB NOT NULL DEFAULT '[]',
    all_items_checked BOOLEAN NOT NULL DEFAULT FALSE,
    briefed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (team_id)
);

CREATE INDEX idx_safety_briefings_incident ON safety_briefings (incident_id);

INSERT INTO schema_migrations (version) VALUES ('004');
