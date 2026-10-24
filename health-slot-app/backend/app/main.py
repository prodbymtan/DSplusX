"""FastAPI entry point.

    cd backend && uvicorn app.main:app --reload --port 8000

If frontend/dist exists (after `npm run build`), the app is also served at
http://localhost:8000, so the whole demo can run from one process.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select

from app.api import appointments, demo, emergency, metrics, patients, slots, ws
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.models.db_models import Clinic
from app.seed import seed
from app.services import offers, risk

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    with SessionLocal() as db:
        empty = db.scalar(select(func.count()).select_from(Clinic)) == 0
    if empty:
        logging.info("Seeding demo data: %s", seed(reset=True))
    risk.load_model()
    yield
    offers.cancel_all_tasks()


app = FastAPI(title="Health Slot Matcher API", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (appointments.router, slots.router, patients.router, metrics.router, demo.router, emergency.router):
    app.include_router(r, prefix="/api")
app.include_router(ws.router)


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "risk_source": risk.risk_source()}


# Serve the built frontend if it exists (single-process demo mode).
if settings.frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=settings.frontend_dist / "assets"), name="assets")

    _dist = settings.frontend_dist.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Not found")
        candidate = (_dist / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(_dist):
            return FileResponse(candidate)
        return FileResponse(_dist / "index.html")
