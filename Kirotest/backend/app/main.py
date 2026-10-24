"""
HealthSlot FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, bookings, slots, webhooks, ws
from app.core.config import settings
from app.core.database import engine
from app.models import *  # noqa: F401, F403 — registers all ORM models with Base

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("HealthSlot API starting up (version %s)", settings.APP_VERSION)
    yield
    await engine.dispose()
    logger.info("HealthSlot API shut down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Real-time healthcare appointment slot recovery API. "
        "Instantly fills no-shows and late cancellations via geofenced standby matching."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth.router,          prefix=API_PREFIX)
app.include_router(slots.router,         prefix=API_PREFIX)
app.include_router(slots.standby_router, prefix=API_PREFIX)
app.include_router(bookings.router,      prefix=API_PREFIX)
app.include_router(webhooks.router,      prefix=API_PREFIX)
app.include_router(ws.router,            prefix=API_PREFIX)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
