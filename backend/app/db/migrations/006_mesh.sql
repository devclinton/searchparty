-- Migration: 006_mesh
-- Description: Mesh network node tracking and message log

CREATE TABLE mesh_nodes (
    node_id TEXT PRIMARY KEY,
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    long_name TEXT,
    short_name TEXT,
    hw_model TEXT,
    battery_level INTEGER,
    last_lat DOUBLE PRECISION,
    last_lon DOUBLE PRECISION,
    last_altitude DOUBLE PRECISION,
    snr DOUBLE PRECISION,
    last_heard_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mesh_nodes_incident ON mesh_nodes (incident_id);

CREATE TABLE mesh_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    from_node TEXT NOT NULL,
    to_node TEXT,
    channel INTEGER NOT NULL DEFAULT 0,
    message_text TEXT NOT NULL,
    is_emergency BOOLEAN NOT NULL DEFAULT FALSE,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mesh_messages_incident ON mesh_messages (incident_id);
CREATE INDEX idx_mesh_messages_emergency ON mesh_messages (is_emergency) WHERE is_emergency = TRUE;

INSERT INTO schema_migrations (version) VALUES ('006');
