-- Migration: 007_drones
-- Description: Drone registry, missions, telemetry, and video metadata

-- Drone registry
CREATE TABLE drones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    model TEXT NOT NULL,
    serial_number TEXT,
    pilot_user_id UUID REFERENCES users(id),
    nickname TEXT,
    status TEXT NOT NULL DEFAULT 'standby' CHECK (status IN (
        'standby', 'flying', 'returning', 'charging', 'maintenance'
    )),
    battery_percent INTEGER,
    has_thermal BOOLEAN NOT NULL DEFAULT FALSE,
    obstacle_avoidance TEXT NOT NULL DEFAULT 'stop' CHECK (
        obstacle_avoidance IN ('stop', 'bypass', 'disabled')
    ),
    camera_fov_h DOUBLE PRECISION,
    camera_fov_v DOUBLE PRECISION,
    sensor_width_mm DOUBLE PRECISION,
    focal_length_mm DOUBLE PRECISION,
    image_width_px INTEGER,
    image_height_px INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_drones_incident ON drones (incident_id);

-- Drone missions (search patterns + flight plans)
CREATE TABLE drone_missions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    drone_id UUID REFERENCES drones(id) ON DELETE SET NULL,
    segment_id UUID REFERENCES search_segments(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    pattern_type TEXT NOT NULL CHECK (pattern_type IN (
        'parallel_track', 'expanding_square', 'sector_search', 'creeping_line', 'custom'
    )),
    status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN (
        'planned', 'exported', 'in_flight', 'completed', 'aborted'
    )),
    altitude_meters DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    speed_ms DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    overlap_percent DOUBLE PRECISION NOT NULL DEFAULT 70.0,
    gimbal_pitch DOUBLE PRECISION NOT NULL DEFAULT -90.0,
    obstacle_avoidance TEXT NOT NULL DEFAULT 'stop',
    waypoints JSONB NOT NULL DEFAULT '[]',
    export_format TEXT,
    area_sq_meters DOUBLE PRECISION,
    estimated_flight_time_seconds DOUBLE PRECISION,
    actual_coverage_percent DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_drone_missions_incident ON drone_missions (incident_id);
CREATE INDEX idx_drone_missions_drone ON drone_missions (drone_id);

-- Video metadata (SRT telemetry linked to external video)
CREATE TABLE video_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    drone_id UUID REFERENCES drones(id) ON DELETE SET NULL,
    mission_id UUID REFERENCES drone_missions(id) ON DELETE SET NULL,
    filename TEXT NOT NULL,
    external_url TEXT,
    duration_seconds DOUBLE PRECISION,
    frame_count INTEGER,
    telemetry JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_video_metadata_incident ON video_metadata (incident_id);

INSERT INTO schema_migrations (version) VALUES ('007');
