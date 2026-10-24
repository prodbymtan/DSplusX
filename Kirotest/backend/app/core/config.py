"""
Application configuration loaded from environment variables.
All sensitive values must be set in a .env file — never hardcoded.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "HealthSlot"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str                          # must be set in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24   # 24 hours

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str                        # postgresql+asyncpg://user:pass@host/db
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Firebase / Push Notifications ────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"

    # ── Geofencing defaults ───────────────────────────────────────────────────
    DEFAULT_STANDBY_RADIUS_METERS: int = 5_000   # 5 km
    NO_SHOW_THRESHOLD_MINUTES: int = 15          # mark no-show after 15 min late

    # ── FHIR / EHR ────────────────────────────────────────────────────────────
    FHIR_BASE_URL: str = ""                  # e.g. https://fhir.epic.com/interconnect-fhir-oauth
    FHIR_CLIENT_ID: str = ""
    FHIR_CLIENT_SECRET: str = ""

    # ── Booking lock ──────────────────────────────────────────────────────────
    BOOKING_LOCK_TTL_SECONDS: int = 30       # hold a slot for 30 s while patient confirms
    STANDBY_BROADCAST_TIMEOUT_SECONDS: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
