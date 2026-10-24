"""Demo helpers: reset everything between rehearsals, and map data."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.db_models import Clinic, Patient
from app.seed import load_seed_file, seed
from app.services import offers
from app.services.broadcaster import broadcaster
from app.services.matching import haversine_miles

router = APIRouter(tags=["demo"])


@router.post("/demo/reset")
async def reset_demo() -> dict:
    offers.cancel_all_tasks()
    summary = await asyncio.to_thread(seed, True)
    await broadcaster.to_everyone({"type": "reset"})
    return summary


def _map() -> dict:
    data = load_seed_file()
    with SessionLocal() as db:
        clinic = db.scalar(select(Clinic))
        patients = db.scalars(select(Patient).order_by(Patient.id)).all()
        hospitals = [
            {**h, "distance_miles": round(haversine_miles(clinic.lat, clinic.lng, h["lat"], h["lng"]), 2)}
            for h in data.get("hospitals", [])
        ]
        return {
            "clinic": {"name": clinic.name, "lat": clinic.lat, "lng": clinic.lng},
            "patients": [
                {"id": p.id, "name": p.name, "lat": p.lat, "lng": p.lng, "radius_miles": p.radius_miles, "is_available": p.is_available}
                for p in patients
            ],
            "hospitals": hospitals,
            "sources": data.get("sources", {}),
        }


@router.get("/map")
async def map_data() -> dict:
    return await asyncio.to_thread(_map)
