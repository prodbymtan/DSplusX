"""Patient-side endpoints: standby list, each phone's current state, standby toggle."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.db_models import Clinic, Offer, Patient, Slot
from app.services.broadcaster import broadcaster
from app.services.matching import eligibility
from app.services.offers import seconds_left, time_label

router = APIRouter(prefix="/patients", tags=["patients"])


class AvailabilityUpdate(BaseModel):
    is_available: bool


def _patient_dict(p: Patient, clinic: Clinic | None) -> dict:
    ok, reason, distance = eligibility(p, clinic) if clinic else (False, "no clinic", 0.0)
    return {
        "id": p.id,
        "name": p.name,
        "lat": p.lat,
        "lng": p.lng,
        "radius_miles": p.radius_miles,
        "insurance": p.insurance,
        "reliability": p.reliability,
        "is_available": p.is_available,
        "distance_miles": round(distance, 2),
        "eligible_now": ok,
        "eligibility_reason": reason,
    }


def _list() -> list[dict]:
    with SessionLocal() as db:
        clinic = db.scalar(select(Clinic))
        return [_patient_dict(p, clinic) for p in db.scalars(select(Patient).order_by(Patient.id)).all()]


def _state(patient_id: int) -> dict | None:
    with SessionLocal() as db:
        p = db.get(Patient, patient_id)
        if p is None:
            return None
        clinic = db.scalar(select(Clinic))
        rows = db.execute(
            select(Offer, Slot).join(Slot, Offer.slot_id == Slot.id).where(Offer.patient_id == patient_id).order_by(Offer.sent_at.desc(), Offer.id.desc())
        ).all()
        active, history = [], []
        for offer, slot in rows:
            item = {
                "slot_id": slot.id,
                "clinic": clinic.name if clinic else "",
                "time_label": time_label(slot.start_time),
                "start_time": slot.start_time.isoformat(),
                "distance_miles": round(offer.distance_miles, 2),
                "round": offer.round,
            }
            if slot.status == "open":
                active.append({**item, "seconds_left": seconds_left(slot)})
            else:
                outcome = "booked" if slot.booked_patient_id == patient_id else ("taken" if slot.status == "booked" else "expired")
                history.append({**item, "outcome": outcome})
        return {"patient": _patient_dict(p, clinic), "offers": active, "history": history[:5]}


@router.get("")
async def list_patients() -> list[dict]:
    return await asyncio.to_thread(_list)


@router.get("/{patient_id}/state")
async def patient_state(patient_id: int) -> dict:
    state = await asyncio.to_thread(_state, patient_id)
    if state is None:
        raise HTTPException(404, "Patient not found.")
    return state


def _set_available(patient_id: int, value: bool) -> bool:
    with SessionLocal() as db:
        p = db.get(Patient, patient_id)
        if p is None:
            return False
        p.is_available = value
        db.commit()
        return True


@router.patch("/{patient_id}")
async def update_availability(patient_id: int, body: AvailabilityUpdate) -> dict:
    if not await asyncio.to_thread(_set_available, patient_id, body.is_available):
        raise HTTPException(404, "Patient not found.")
    await broadcaster.to_patient(patient_id, {"type": "patient_updated"})
    await broadcaster.to_clinic({"type": "patient_updated", "patient_id": patient_id})
    return await patient_state(patient_id)
