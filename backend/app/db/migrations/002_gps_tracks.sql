-- Migration: 002_gps_tracks
-- Description: Create GPS tracks and points tables

CREATE TABLE gps_tracks (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    point_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gps_tracks_incident ON gps_tracks (incident_id);
CREATE INDEX idx_gps_tracks_user ON gps_tracks (user_id);
CREATE INDEX idx_gps_tracks_team ON gps_tracks (team_id);

CREATE TABLE gps_points (
    id BIGSERIAL PRIMARY KEY,
    track_id TEXT NOT NULL REFERENCES gps_tracks(id) ON DELETE CASCADE,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    altitude DOUBLE PRECISION,
    accuracy DOUBLE PRECISION NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    point GEOMETRY(Point, 4326)
);

CREATE INDEX idx_gps_points_track ON gps_points (track_id);
CREATE INDEX idx_gps_points_spatial ON gps_points USING GIST (point);

INSERT INTO schema_migrations (version) VALUES ('002');
