"""Settings, read from environment variables (or backend/.env if you create one)."""
from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


def _load_dotenv() -> None:
    """Tiny .env loader so we don't need python-dotenv. KEY=VALUE per line."""
    env = BACKEND_DIR / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


class Settings:
    # SQLite by default (zero setup). For Postgres/PostGIS see database/docker-compose.yml:
    # DATABASE_URL=postgresql+psycopg://health:health@localhost:5432/health_slot
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'health_slot.db'}")

    model_path: Path = Path(os.getenv("MODEL_PATH", REPO_ROOT / "ml" / "artifacts" / "model.pkl"))
    metrics_path: Path = Path(os.getenv("METRICS_PATH", REPO_ROOT / "ml" / "artifacts" / "metrics.json"))
    ml_src: Path = REPO_ROOT / "ml" / "src"

    # How long each round of offers stays open before the radius expands.
    offer_window_seconds: float = float(os.getenv("OFFER_WINDOW_SECONDS", "120"))
    # Number of times the search radius grows before the slot expires.
    ripple_rounds: int = int(os.getenv("RIPPLE_ROUNDS", "2"))
    # Each ripple round multiplies every patient's radius by this.
    radius_growth: float = float(os.getenv("RADIUS_GROWTH", "2.0"))

    frontend_dist: Path = REPO_ROOT / "frontend" / "dist"
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")


settings = Settings()
