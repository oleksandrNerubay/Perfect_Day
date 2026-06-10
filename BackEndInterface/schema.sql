CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    age         INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    interests           TEXT[]  NOT NULL DEFAULT '{}',
    interest_weights    JSONB   NOT NULL DEFAULT '{}',
    feedback_scores     JSONB   NOT NULL DEFAULT '{}',
    session_count       INTEGER NOT NULL DEFAULT 0,
    total_time_spent_sec INTEGER NOT NULL DEFAULT 0,
    last_active         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    segment             VARCHAR(50),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
