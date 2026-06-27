-- =============================================================================
--  Health Insights System — Database Initialisation
--  Runs automatically on first container start via /docker-entrypoint-initdb.d/
--  File: 01_schema.sql
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";  -- slow query analysis

-- Timezone
SET timezone = 'UTC';


-- =============================================================================
--  USERS
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id     TEXT UNIQUE,                         -- wearable device ID / OAuth sub
    email           TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    first_name      TEXT,
    last_name       TEXT,
    date_of_birth   DATE,
    biological_sex  TEXT CHECK (biological_sex IN ('male','female','other','prefer_not_to_say')),
    height_cm       NUMERIC(5,1) CHECK (height_cm BETWEEN 50 AND 300),
    weight_kg       NUMERIC(5,1) CHECK (weight_kg BETWEEN 10 AND 500),
    bmi             NUMERIC(4,1) GENERATED ALWAYS AS (
                        ROUND((weight_kg / ((height_cm / 100.0) ^ 2))::NUMERIC, 1)
                    ) STORED,
    goals           TEXT[]       DEFAULT '{}',           -- e.g. '{sleep,activity}'
    conditions      TEXT[]       DEFAULT '{}',
    timezone        TEXT         DEFAULT 'UTC',
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ                          -- soft delete
);

CREATE INDEX idx_users_email       ON users (email)      WHERE deleted_at IS NULL;
CREATE INDEX idx_users_external_id ON users (external_id) WHERE external_id IS NOT NULL;


-- =============================================================================
--  WEARABLE CONNECTIONS
-- =============================================================================

CREATE TABLE IF NOT EXISTS wearable_connections (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider     TEXT NOT NULL CHECK (provider IN ('fitbit','apple_health','garmin','whoop','manual')),
    access_token TEXT,                                   -- encrypted at app layer
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    last_sync_at TIMESTAMPTZ,
    is_active    BOOLEAN DEFAULT TRUE,
    UNIQUE (user_id, provider)
);

CREATE INDEX idx_wearable_user ON wearable_connections (user_id, is_active);


-- =============================================================================
--  HEALTH METRICS  (one row per daily snapshot per user)
-- =============================================================================

CREATE TABLE IF NOT EXISTS health_metrics (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recorded_date   DATE NOT NULL,
    source          TEXT DEFAULT 'manual',               -- 'fitbit' | 'apple_health' | 'manual' …

    -- Sleep
    sleep_hours     NUMERIC(4,1) CHECK (sleep_hours BETWEEN 0 AND 24),
    sleep_quality   NUMERIC(3,1) CHECK (sleep_quality BETWEEN 1 AND 10),
    deep_sleep_hrs  NUMERIC(4,1),
    rem_sleep_hrs   NUMERIC(4,1),

    -- Activity
    steps_daily     INTEGER      CHECK (steps_daily >= 0),
    active_minutes  INTEGER      CHECK (active_minutes >= 0),
    calories_burned INTEGER      CHECK (calories_burned >= 0),
    distance_km     NUMERIC(6,2),

    -- Cardiovascular
    resting_hr      INTEGER      CHECK (resting_hr BETWEEN 20 AND 300),
    hrv             NUMERIC(6,1) CHECK (hrv > 0),
    blood_oxygen    NUMERIC(4,1) CHECK (blood_oxygen BETWEEN 50 AND 100),

    -- Stress & lifestyle
    stress_index    NUMERIC(5,1) CHECK (stress_index BETWEEN 0 AND 100),
    water_intake    NUMERIC(4,2) CHECK (water_intake >= 0),
    mood_score      SMALLINT     CHECK (mood_score BETWEEN 1 AND 10),

    -- Audit
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (user_id, recorded_date)
);

CREATE INDEX idx_metrics_user_date   ON health_metrics (user_id, recorded_date DESC);
CREATE INDEX idx_metrics_recorded    ON health_metrics (recorded_date DESC);
CREATE INDEX idx_metrics_source      ON health_metrics (source);


-- =============================================================================
--  HEALTH SCORES  (model predictions stored for auditability)
-- =============================================================================

CREATE TABLE IF NOT EXISTS health_scores (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metrics_id      UUID REFERENCES health_metrics(id) ON DELETE SET NULL,
    scored_at       TIMESTAMPTZ DEFAULT NOW(),

    -- Prediction
    health_score    NUMERIC(5,2) NOT NULL CHECK (health_score BETWEEN 0 AND 100),
    risk_level      TEXT NOT NULL CHECK (risk_level IN ('low','moderate','high','critical')),
    confidence      NUMERIC(4,3) CHECK (confidence BETWEEN 0 AND 1),
    model_version   TEXT NOT NULL,

    -- Domain breakdown (JSONB for schema flexibility)
    domain_scores   JSONB DEFAULT '{}',

    -- Recommendations (array of JSONB objects)
    recommendations JSONB DEFAULT '[]'
);

CREATE INDEX idx_scores_user_date  ON health_scores (user_id, scored_at DESC);
CREATE INDEX idx_scores_risk       ON health_scores (risk_level, scored_at DESC);
CREATE INDEX idx_scores_gin        ON health_scores USING gin (domain_scores);


-- =============================================================================
--  RECOMMENDATIONS LOG
-- =============================================================================

CREATE TABLE IF NOT EXISTS recommendation_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score_id        UUID REFERENCES health_scores(id) ON DELETE SET NULL,
    domain          TEXT NOT NULL,
    message         TEXT NOT NULL,
    priority        TEXT CHECK (priority IN ('high','medium','low')),
    ab_variant      TEXT,
    sent_at         TIMESTAMPTZ DEFAULT NOW(),
    opened_at       TIMESTAMPTZ,
    acted_at        TIMESTAMPTZ,
    dismissed_at    TIMESTAMPTZ
);

CREATE INDEX idx_recs_user       ON recommendation_events (user_id, sent_at DESC);
CREATE INDEX idx_recs_domain     ON recommendation_events (domain, priority);


-- =============================================================================
--  AUDIT LOG  (HIPAA requirement)
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGSERIAL PRIMARY KEY,
    event_time  TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    actor_id    UUID,                                    -- NULL = system/anonymous
    actor_type  TEXT DEFAULT 'user',                     -- 'user' | 'system' | 'admin'
    action      TEXT NOT NULL,                           -- 'predict' | 'view_data' | 'delete' …
    resource    TEXT,
    resource_id TEXT,
    ip_address  INET,
    user_agent  TEXT,
    status      TEXT DEFAULT 'ok',
    detail      JSONB DEFAULT '{}'
) PARTITION BY RANGE (event_time);

-- Monthly partitions for audit log (pre-create 12 months)
CREATE TABLE audit_log_2025_01 PARTITION OF audit_log FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE audit_log_2025_06 PARTITION OF audit_log FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');
CREATE TABLE audit_log_2025_07 PARTITION OF audit_log FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');
CREATE TABLE audit_log_2025_08 PARTITION OF audit_log FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
CREATE TABLE audit_log_2025_09 PARTITION OF audit_log FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
CREATE TABLE audit_log_2025_10 PARTITION OF audit_log FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
CREATE TABLE audit_log_2025_11 PARTITION OF audit_log FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
CREATE TABLE audit_log_2025_12 PARTITION OF audit_log FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
CREATE TABLE audit_log_2026_01 PARTITION OF audit_log FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE audit_log_2026_06 PARTITION OF audit_log FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE audit_log_2026_07 PARTITION OF audit_log FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE audit_log_2026_12 PARTITION OF audit_log FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

CREATE INDEX idx_audit_time   ON audit_log (event_time DESC);
CREATE INDEX idx_audit_actor  ON audit_log (actor_id, event_time DESC);
CREATE INDEX idx_audit_action ON audit_log (action, event_time DESC);


-- =============================================================================
--  UPDATED_AT TRIGGER (auto-update timestamps)
-- =============================================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_metrics_updated_at
    BEFORE UPDATE ON health_metrics
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- =============================================================================
--  ROW-LEVEL SECURITY  (HIPAA data isolation)
-- =============================================================================

ALTER TABLE health_metrics        ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_scores         ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendation_events ENABLE ROW LEVEL SECURITY;

-- App role sees only its own rows (set app.current_user_id at session level)
CREATE POLICY metrics_owner ON health_metrics
    USING (user_id = current_setting('app.current_user_id', TRUE)::UUID);

CREATE POLICY scores_owner ON health_scores
    USING (user_id = current_setting('app.current_user_id', TRUE)::UUID);

CREATE POLICY recs_owner ON recommendation_events
    USING (user_id = current_setting('app.current_user_id', TRUE)::UUID);


-- =============================================================================
--  APP ROLE  (least-privilege database user for the API)
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'health_app') THEN
        CREATE ROLE health_app LOGIN PASSWORD 'changeme_in_env';
    END IF;
END$$;

GRANT CONNECT ON DATABASE health_insights TO health_app;
GRANT USAGE   ON SCHEMA public TO health_app;
GRANT SELECT, INSERT, UPDATE, DELETE
    ON users, health_metrics, health_scores,
       recommendation_events, wearable_connections
    TO health_app;
GRANT INSERT ON audit_log TO health_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO health_app;
