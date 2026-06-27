-- ============================================================
--  Personalized Health Insights System — PostgreSQL Schema
--  Normalization: 3NF throughout
--  Requires: PostgreSQL 14+, pgcrypto extension
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────
--  ENUMS
-- ─────────────────────────────────────────

CREATE TYPE user_role      AS ENUM ('user', 'admin', 'clinician');
CREATE TYPE gender_type    AS ENUM ('male', 'female', 'non_binary', 'prefer_not_to_say');
CREATE TYPE activity_level AS ENUM ('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extra_active');
CREATE TYPE meal_type      AS ENUM ('breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout');
CREATE TYPE rec_category   AS ENUM ('sleep', 'activity', 'nutrition', 'hydration', 'stress', 'general');
CREATE TYPE rec_priority   AS ENUM ('low', 'medium', 'high');
CREATE TYPE notif_type     AS ENUM ('reminder', 'insight', 'achievement', 'alert', 'system');
CREATE TYPE notif_channel  AS ENUM ('push', 'email', 'in_app', 'sms');


-- ─────────────────────────────────────────
--  MODULE 1: USER AUTHENTICATION
-- ─────────────────────────────────────────

CREATE TABLE users (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            user_role    NOT NULL DEFAULT 'user',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN      NOT NULL DEFAULT FALSE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE INDEX idx_users_email    ON users (email);
CREATE INDEX idx_users_role     ON users (role);
CREATE INDEX idx_users_active   ON users (is_active);

COMMENT ON TABLE  users                IS 'Core identity table. Credentials only — profile data in user_profiles.';
COMMENT ON COLUMN users.password_hash  IS 'bcrypt hash, never plain text.';


CREATE TABLE refresh_tokens (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID         NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL,
    expires_at  TIMESTAMPTZ  NOT NULL,
    is_revoked  BOOLEAN      NOT NULL DEFAULT FALSE,
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_refresh_token UNIQUE (token_hash)
);

CREATE INDEX idx_refresh_tokens_user_id    ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens (expires_at);

COMMENT ON TABLE refresh_tokens IS 'Hashed refresh tokens; rotate on every use, delete on logout.';


-- ─────────────────────────────────────────
--  MODULE 2: USER PROFILE
-- ─────────────────────────────────────────

CREATE TABLE user_profiles (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID          NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    first_name          VARCHAR(100)  NOT NULL,
    last_name           VARCHAR(100)  NOT NULL,
    date_of_birth       DATE,
    gender              gender_type,
    height_cm           NUMERIC(5,2)  CHECK (height_cm > 0 AND height_cm < 300),
    weight_kg           NUMERIC(5,2)  CHECK (weight_kg > 0 AND weight_kg < 700),
    activity_level      activity_level,
    health_goals        TEXT[],
    medical_conditions  TEXT[],
    avatar_url          TEXT,
    timezone            VARCHAR(60)   DEFAULT 'UTC',
    updated_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_profiles_user_id UNIQUE (user_id)
);

COMMENT ON TABLE  user_profiles               IS '1:1 with users. Separated to keep users table lean (2NF).';
COMMENT ON COLUMN user_profiles.health_goals  IS 'e.g. {"lose_weight","improve_sleep","build_muscle"}';


-- ─────────────────────────────────────────
--  MODULE 3: DAILY HEALTH LOGS
-- ─────────────────────────────────────────

CREATE TABLE health_logs (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    log_date      DATE        NOT NULL,
    mood_score    SMALLINT    CHECK (mood_score BETWEEN 1 AND 10),
    stress_level  SMALLINT    CHECK (stress_level BETWEEN 1 AND 10),
    energy_level  SMALLINT    CHECK (energy_level BETWEEN 1 AND 10),
    water_ml      INTEGER     CHECK (water_ml >= 0),
    notes         TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_health_log_user_date UNIQUE (user_id, log_date)
);

CREATE INDEX idx_health_logs_user_id  ON health_logs (user_id);
CREATE INDEX idx_health_logs_date     ON health_logs (log_date DESC);
CREATE INDEX idx_health_logs_user_date ON health_logs (user_id, log_date DESC);

COMMENT ON TABLE  health_logs            IS 'One row per user per calendar day.';
COMMENT ON COLUMN health_logs.water_ml   IS 'Total daily water intake in millilitres.';


-- ─────────────────────────────────────────
--  MODULE 4: SLEEP TRACKING
-- ─────────────────────────────────────────

CREATE TABLE sleep_logs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    sleep_date      DATE        NOT NULL,
    bedtime         TIMESTAMPTZ NOT NULL,
    wake_time       TIMESTAMPTZ NOT NULL,
    duration_min    INTEGER     GENERATED ALWAYS AS
                        (EXTRACT(EPOCH FROM (wake_time - bedtime)) / 60)::INTEGER
                    STORED,
    quality_score   SMALLINT    CHECK (quality_score BETWEEN 1 AND 10),
    sleep_stages    JSONB,
    interruptions   SMALLINT    DEFAULT 0 CHECK (interruptions >= 0),
    source          VARCHAR(30) DEFAULT 'manual',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_sleep_wake_after_bed CHECK (wake_time > bedtime)
);

CREATE INDEX idx_sleep_logs_user_id  ON sleep_logs (user_id);
CREATE INDEX idx_sleep_logs_date     ON sleep_logs (sleep_date DESC);
CREATE INDEX idx_sleep_stages_gin    ON sleep_logs USING GIN (sleep_stages);

COMMENT ON TABLE  sleep_logs               IS 'One row per sleep session; duration computed via GENERATED STORED column.';
COMMENT ON COLUMN sleep_logs.sleep_stages  IS 'JSONB e.g. {"deep_min":90,"light_min":180,"rem_min":60,"awake_min":10}';
COMMENT ON COLUMN sleep_logs.source        IS 'manual | fitbit | apple_health | garmin';


-- ─────────────────────────────────────────
--  MODULE 5: ACTIVITY TRACKING
-- ─────────────────────────────────────────

CREATE TABLE activity_logs (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID         NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    activity_date   DATE         NOT NULL,
    activity_type   VARCHAR(50)  NOT NULL,
    duration_min    INTEGER      CHECK (duration_min > 0),
    distance_m      INTEGER      CHECK (distance_m >= 0),
    calories_burned INTEGER      CHECK (calories_burned >= 0),
    intensity       SMALLINT     CHECK (intensity BETWEEN 1 AND 5),
    steps           INTEGER      CHECK (steps >= 0),
    avg_heart_rate  NUMERIC(5,2) CHECK (avg_heart_rate > 0),
    max_heart_rate  NUMERIC(5,2),
    source          VARCHAR(30)  DEFAULT 'manual',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_activity_logs_user_id    ON activity_logs (user_id);
CREATE INDEX idx_activity_logs_date       ON activity_logs (activity_date DESC);
CREATE INDEX idx_activity_logs_user_date  ON activity_logs (user_id, activity_date DESC);
CREATE INDEX idx_activity_logs_type       ON activity_logs (activity_type);

COMMENT ON TABLE  activity_logs              IS 'Multiple activities per day supported (e.g. morning run + evening yoga).';
COMMENT ON COLUMN activity_logs.intensity    IS '1=very_light 2=light 3=moderate 4=vigorous 5=max';


-- ─────────────────────────────────────────
--  MODULE 6: NUTRITION TRACKING
-- ─────────────────────────────────────────

CREATE TABLE nutrition_logs (
    id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID          NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    log_date        DATE          NOT NULL,
    meal_type       meal_type     NOT NULL,
    total_calories  INTEGER       CHECK (total_calories >= 0),
    total_protein_g NUMERIC(6,2)  CHECK (total_protein_g >= 0),
    total_carbs_g   NUMERIC(6,2)  CHECK (total_carbs_g >= 0),
    total_fat_g     NUMERIC(6,2)  CHECK (total_fat_g >= 0),
    total_fiber_g   NUMERIC(6,2)  CHECK (total_fiber_g >= 0),
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_nutrition_logs_user_id    ON nutrition_logs (user_id);
CREATE INDEX idx_nutrition_logs_date       ON nutrition_logs (log_date DESC);
CREATE INDEX idx_nutrition_logs_user_date  ON nutrition_logs (user_id, log_date DESC);

COMMENT ON TABLE nutrition_logs IS 'Meal-level header. Macro totals are denormalized here for fast daily queries; items are in nutrition_items.';


CREATE TABLE nutrition_items (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    nutrition_log_id UUID         NOT NULL REFERENCES nutrition_logs (id) ON DELETE CASCADE,
    food_name        VARCHAR(200) NOT NULL,
    serving_qty      NUMERIC(6,2) NOT NULL CHECK (serving_qty > 0),
    serving_unit     VARCHAR(30)  NOT NULL,
    calories         INTEGER      CHECK (calories >= 0),
    protein_g        NUMERIC(6,2) CHECK (protein_g >= 0),
    carbs_g          NUMERIC(6,2) CHECK (carbs_g >= 0),
    fat_g            NUMERIC(6,2) CHECK (fat_g >= 0),
    fiber_g          NUMERIC(6,2) CHECK (fiber_g >= 0),
    sodium_mg        NUMERIC(7,2),
    sugar_g          NUMERIC(6,2)
);

CREATE INDEX idx_nutrition_items_log_id ON nutrition_items (nutrition_log_id);

COMMENT ON TABLE nutrition_items IS 'Line items per meal. Eliminates repeating food groups (1NF). Linked to nutrition_logs by FK.';


-- ─────────────────────────────────────────
--  MODULE 7: RECOMMENDATIONS
-- ─────────────────────────────────────────

CREATE TABLE recommendations (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID          NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    category         rec_category  NOT NULL,
    priority         rec_priority  NOT NULL DEFAULT 'medium',
    title            TEXT          NOT NULL,
    content          TEXT          NOT NULL,
    confidence_score NUMERIC(4,3)  CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    model_version    VARCHAR(30),
    is_read          BOOLEAN       NOT NULL DEFAULT FALSE,
    is_dismissed     BOOLEAN       NOT NULL DEFAULT FALSE,
    generated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    expires_at       TIMESTAMPTZ
);

CREATE INDEX idx_recommendations_user_id      ON recommendations (user_id);
CREATE INDEX idx_recommendations_category     ON recommendations (category);
CREATE INDEX idx_recommendations_generated_at ON recommendations (generated_at DESC);
CREATE INDEX idx_recommendations_unread       ON recommendations (user_id, is_read)
    WHERE is_read = FALSE AND is_dismissed = FALSE;

COMMENT ON TABLE  recommendations                  IS 'ML-generated, per category. Partial index on unread for fast inbox queries.';
COMMENT ON COLUMN recommendations.confidence_score IS '0.0–1.0 from Scikit-learn model output.';


CREATE TABLE recommendation_actions (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID        NOT NULL REFERENCES recommendations (id) ON DELETE CASCADE,
    action_text       TEXT        NOT NULL,
    sort_order        SMALLINT    NOT NULL,
    is_completed      BOOLEAN     NOT NULL DEFAULT FALSE,
    completed_at      TIMESTAMPTZ
);

CREATE INDEX idx_rec_actions_rec_id ON recommendation_actions (recommendation_id);

COMMENT ON TABLE recommendation_actions IS 'Ordered action steps per recommendation. Separates multi-valued actions (1NF).';


-- ─────────────────────────────────────────
--  MODULE 8: NOTIFICATIONS
-- ─────────────────────────────────────────

CREATE TABLE notifications (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID          NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    type          notif_type    NOT NULL,
    channel       notif_channel NOT NULL,
    title         TEXT          NOT NULL,
    body          TEXT,
    metadata      JSONB,
    is_read       BOOLEAN       NOT NULL DEFAULT FALSE,
    scheduled_at  TIMESTAMPTZ,
    sent_at       TIMESTAMPTZ,
    read_at       TIMESTAMPTZ,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id      ON notifications (user_id);
CREATE INDEX idx_notifications_scheduled_at ON notifications (scheduled_at)
    WHERE sent_at IS NULL;
CREATE INDEX idx_notifications_unread       ON notifications (user_id, is_read)
    WHERE is_read = FALSE;
CREATE INDEX idx_notifications_metadata_gin ON notifications USING GIN (metadata);

COMMENT ON TABLE  notifications          IS 'Multi-channel notification queue. metadata JSONB holds channel-specific payload.';
COMMENT ON COLUMN notifications.metadata IS 'e.g. {"deep_link":"/insights/abc123","badge_count":3}';


-- ─────────────────────────────────────────
--  UPDATED_AT TRIGGER
-- ─────────────────────────────────────────

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

CREATE TRIGGER trg_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
