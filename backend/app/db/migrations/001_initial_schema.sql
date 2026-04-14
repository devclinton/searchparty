-- Migration: 001_initial_schema
-- Description: Create users, incidents, and teams tables

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Migration tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT,
    oauth_provider TEXT,
    oauth_id TEXT,
    contact_phone TEXT,
    sar_qualifications TEXT[],
    preferred_locale TEXT NOT NULL DEFAULT 'en',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_users_oauth ON users (oauth_provider, oauth_id) WHERE oauth_provider IS NOT NULL;

-- Incidents (search operations)
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planning' CHECK (status IN ('planning', 'active', 'suspended', 'closed')),
    description TEXT,
    -- Subject info
    subject_name TEXT,
    subject_age_category TEXT CHECK (subject_age_category IN (
        'child_1_3', 'child_4_6', 'child_7_12', 'child_13_15',
        'adult', 'elderly'
    )),
    subject_activity TEXT CHECK (subject_activity IN (
        'hiker', 'hunter', 'berry_picker', 'fisher',
        'climber', 'skier', 'runner', 'dementia',
        'despondent', 'other'
    )),
    subject_condition TEXT,
    subject_clothing TEXT,
    subject_medical_needs TEXT,
    -- Location
    ipp_lat DOUBLE PRECISION,
    ipp_lon DOUBLE PRECISION,
    ipp_point GEOMETRY(Point, 4326),
    terrain_type TEXT,
    -- Metadata
    incident_commander_id UUID REFERENCES users(id),
    data_retention_days INTEGER NOT NULL DEFAULT 90,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

CREATE INDEX idx_incidents_status ON incidents (status);
CREATE INDEX idx_incidents_commander ON incidents (incident_commander_id);

-- Teams
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'standby' CHECK (status IN ('standby', 'deployed', 'returning', 'overdue', 'stood_down')),
    leader_id UUID REFERENCES users(id),
    search_type TEXT CHECK (search_type IN ('hasty', 'grid', 'line', 'attraction')),
    check_in_interval_minutes INTEGER NOT NULL DEFAULT 30,
    last_check_in_at TIMESTAMPTZ,
    deployed_at TIMESTAMPTZ,
    turnaround_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_teams_incident ON teams (incident_id);
CREATE INDEX idx_teams_status ON teams (status);

-- Team members (join table with ICS roles)
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    role TEXT NOT NULL DEFAULT 'searcher' CHECK (role IN (
        'incident_commander', 'operations_chief', 'division_supervisor',
        'team_leader', 'searcher', 'safety_officer'
    )),
    signed_in_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    signed_out_at TIMESTAMPTZ,
    UNIQUE (team_id, user_id)
);

CREATE INDEX idx_team_members_team ON team_members (team_id);
CREATE INDEX idx_team_members_user ON team_members (user_id);

INSERT INTO schema_migrations (version) VALUES ('001');
