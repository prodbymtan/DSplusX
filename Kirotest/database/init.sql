-- ============================================================
-- HealthSlot Database Initialization
-- Run once against a fresh PostgreSQL instance.
-- Requires PostGIS extension.
-- ============================================================

-- Enable PostGIS for geospatial queries
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Enums ────────────────────────────────────────────────────
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('patient', 'clinic_staff', 'clinic_admin');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE appointment_type AS ENUM ('new_patient', 'follow_up', 'urgent', 'telehealth');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE slot_status AS ENUM ('available', 'locked', 'booked', 'no_show', 'completed', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE booking_status AS ENUM (
        'confirmed', 'cancelled_by_patient', 'cancelled_by_clinic', 'attended', 'no_show'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ── Users ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    phone           VARCHAR(20),
    role            user_role NOT NULL DEFAULT 'patient',
    fcm_token       VARCHAR(512),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ── Clinics ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clinics (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    address     VARCHAR(512) NOT NULL,
    phone       VARCHAR(20),
    specialty   VARCHAR(100),
    -- PostGIS geography point (lng, lat) — SRID 4326
    location    GEOGRAPHY(POINT, 4326) NOT NULL,
    ehr_system  VARCHAR(50),
    ehr_org_id  VARCHAR(255),
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Spatial index for ST_DWithin radius queries
CREATE INDEX IF NOT EXISTS idx_clinics_location ON clinics USING GIST (location);

-- ── Providers ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS providers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id       UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    full_name       VARCHAR(255) NOT NULL,
    specialty       VARCHAR(100),
    ehr_provider_id VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_providers_clinic ON providers (clinic_id);

-- ── Appointment Slots ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS appointment_slots (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id        UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    provider_id      UUID NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    start_time       TIMESTAMPTZ NOT NULL,
    end_time         TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER NOT NULL,
    appointment_type appointment_type NOT NULL DEFAULT 'follow_up',
    status           slot_status NOT NULL DEFAULT 'available',
    ehr_slot_id      VARCHAR(255),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_slot_times CHECK (end_time > start_time)
);
CREATE INDEX IF NOT EXISTS idx_slots_status       ON appointment_slots (status);
CREATE INDEX IF NOT EXISTS idx_slots_start_time   ON appointment_slots (start_time);
CREATE INDEX IF NOT EXISTS idx_slots_clinic       ON appointment_slots (clinic_id);
CREATE INDEX IF NOT EXISTS idx_slots_ehr_slot_id  ON appointment_slots (ehr_slot_id);

-- ── Bookings ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bookings (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slot_id      UUID UNIQUE NOT NULL REFERENCES appointment_slots(id) ON DELETE CASCADE,
    patient_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status       booking_status NOT NULL DEFAULT 'confirmed',
    notes        TEXT,
    confirmed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_bookings_patient ON bookings (patient_id);

-- ── Trigger: auto-update updated_at ───────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER trg_slots_updated_at
    BEFORE UPDATE ON appointment_slots FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER trg_bookings_updated_at
    BEFORE UPDATE ON bookings FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── Seed data (dev only) ──────────────────────────────────────
-- Inserts a sample clinic in downtown Boston (Lon, Lat order for PostGIS)
INSERT INTO clinics (name, address, specialty, location, ehr_system) VALUES
(
    'Boston General Primary Care',
    '100 Federal St, Boston, MA 02110',
    'primary_care',
    ST_SetSRID(ST_MakePoint(-71.0570, 42.3554), 4326),
    'epic'
)
ON CONFLICT DO NOTHING;
