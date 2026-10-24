"""Clinic-side endpoints: today's schedule with risk scores, and releasing slots."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.db_models import Appointment, Clinic
from app.services import offers, risk
from app.services.offers import ServiceError, slot_summary, time_label

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _schedule() -> dict:
    threshold = risk.high_risk_threshold()
    with SessionLocal() as db:
        clinic = db.scalar(select(Clinic))
        appts = db.scalars(select(Appointment).order_by(Appointment.start_time)).all()
        return {
            "clinic": {"id": clinic.id, "name": clinic.name, "lat": clinic.lat, "lng": clinic.lng} if clinic else None,
            "risk_source": risk.risk_source(),
            "high_risk_threshold": round(threshold, 4),
            "appointments": [
                {
                    "id": a.id,
                    "patient_label": a.patient_label,
                    "start_time": a.start_time.isoformat(),
                    "time_label": time_label(a.start_time),
                    "duration_min": a.duration_min,
                    "age": a.age,
                    "lead_days": (a.start_time.date() - a.booked_at.date()).days,
                    "prior_appts": a.prior_appts,
                    "prior_noshows": a.prior_noshows,
                    "risk": round(a.risk, 4),
                    "high_risk": a.risk >= threshold,
                    "status": a.status,
                    "slot": slot_summary(db, a.slot) if a.slot else None,
                }
                for a in appts
            ],
        }


@router.get("")
async def list_appointments() -> dict:
    return await asyncio.to_thread(_schedule)


async def _release(appointment_id: int, reason: str) -> dict:
    try:
        return await offers.open_slot(appointment_id, reason)
    except ServiceError as e:
        raise HTTPException(e.status_code, e.detail) from e


@router.post("/{appointment_id}/no-show")
async def mark_no_show(appointment_id: int) -> dict:
    return await _release(appointment_id, "no_show")


@router.post("/{appointment_id}/cancel")
async def cancel(appointment_id: int) -> dict:
    return await _release(appointment_id, "cancelled")


@router.post("/{appointment_id}/unconfirmed")
async def unconfirmed(appointment_id: int) -> dict:
    """High-risk patient was asked to confirm and didn't reply by 30 minutes before."""
    return await _release(appointment_id, "unconfirmed")
