"""Emergency Mode: nearest ER from ml/data/ma_hospitals.csv.

EMTALA / No Surprises Act (decision #14): emergency care never depends on
insurance, so this endpoint has NO insurance filter of any kind. It always
returns the nearest emergency department by straight-line distance.
"""
from __future__ import annotations

import asyncio
import csv

from fastapi import APIRouter

from app.core.config import REPO_ROOT
from app.services.matching import haversine_miles

router = APIRouter(prefix="/emergency", tags=["emergency"])

_HOSPITALS_CSV = REPO_ROOT / "ml" / "data" / "ma_hospitals.csv"


def _nearest_ers(lat: float, lon: float) -> list[dict]:
    """ERs sorted by straight-line distance from (lat, lon), nearest first."""
    ers: list[dict] = []
    with _HOSPITALS_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["emergency_dept"] != "Yes":
                continue
            er_lat, er_lon = float(row["lat"]), float(row["lon"])
            distance = haversine_miles(lat, lon, er_lat, er_lon)
            ers.append(
                {
                    "name": row["name"],
                    "municipality": row["municipality"],
                    "county": row["county"],
                    "lat": er_lat,
                    "lon": er_lon,
                    "distance_miles": round(distance, 1),
                }
            )
    ers.sort(key=lambda e: e["distance_miles"])
    return ers


@router.get("/nearest-er")
async def nearest_er(lat: float, lon: float) -> dict:
    ers = await asyncio.to_thread(_nearest_ers, lat, lon)
    return {
        "query": {"lat": lat, "lon": lon},
        "nearest": ers[0] if ers else None,
        "top3": ers[:3],
    }
