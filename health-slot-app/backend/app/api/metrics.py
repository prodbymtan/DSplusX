"""Model + simulation metrics (from ml/artifacts/metrics.json) plus live demo counters."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.db_models import Appointment, Slot

router = APIRouter(prefix="/metrics", tags=["metrics"])

HEADLINE_KEYS = [
    "model_name",
    "auc",
    "brier",
    "top20_catch_rate",
    "fill_rate_baseline",
    "fill_rate_ours",
    "slots_recovered",
    "slots_recovered_per_100_appts",
    "double_bookings_per_100_appts",
    "high_risk_threshold",
    "base_noshow_rate",
    "n_train",
    "n_test",
    "test_period",
    "assumptions",
    "definitions",
    "massachusetts",
]


def _model_metrics() -> dict:
    try:
        data = json.loads(settings.metrics_path.read_text())
    except (OSError, json.JSONDecodeError):
        return {"available": False}
    out = {k: data[k] for k in HEADLINE_KEYS if k in data}
    policies = data.get("policies", {})
    out["refills_per_double_booking"] = {
        "model": policies.get("model", {}).get("recovered_per_conflict"),
        "random": policies.get("random", {}).get("recovered_per_conflict"),
    }
    out["available"] = True
    return out


def _live() -> dict:
    with SessionLocal() as db:
        counts = dict(db.execute(select(Slot.status, func.count()).group_by(Slot.status)).all())
        minutes = db.scalar(
            select(func.coalesce(func.sum(Appointment.duration_min), 0))
            .join(Slot, Slot.appointment_id == Appointment.id)
            .where(Slot.status == "booked")
        )
        return {
            "slots_released": int(sum(counts.values())),
            "slots_recovered": int(counts.get("booked", 0)),
            "slots_open": int(counts.get("open", 0)),
            "slots_expired": int(counts.get("expired", 0)),
            "minutes_recovered": int(minutes or 0),
        }


@router.get("")
async def get_metrics() -> dict:
    model, live = await asyncio.gather(asyncio.to_thread(_model_metrics), asyncio.to_thread(_live))
    return {"model": model, "live": live}
