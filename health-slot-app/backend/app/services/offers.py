"""The core workflow: release a slot, offer it, ripple outward, claim it.

Database work runs in worker threads (`asyncio.to_thread`) with its own session,
and returns plain dicts. WebSocket pushes happen on the event loop.

Race safety: claiming is ONE conditional UPDATE
    UPDATE slots SET status='booked' ... WHERE id=:id AND status='open'
The database applies it atomically, so if 20 people tap "Claim" in the same
millisecond, exactly one row update succeeds and everyone else gets 409.
This works the same on SQLite and Postgres (no SELECT ... FOR UPDATE needed).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, update

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.db_models import Appointment, Clinic, Offer, Patient, Slot
from app.services.broadcaster import broadcaster
from app.services.matching import haversine_miles, rank_candidates

log = logging.getLogger(__name__)

REASON_LABELS = {"no_show": "no-show", "cancelled": "cancellation", "unconfirmed": "no reply to confirmation"}

# slot_id -> running ripple task (kept so tasks aren't garbage-collected and can be cancelled)
_tasks: dict[int, asyncio.Task] = {}


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def now() -> datetime:
    return datetime.now().replace(microsecond=0)


def time_label(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


def seconds_left(slot: Slot) -> int:
    if slot.status != "open":
        return 0
    return max(0, int((slot.expires_at - datetime.now()).total_seconds()))


def slot_summary(db, slot: Slot) -> dict:
    offers = db.scalars(select(Offer).where(Offer.slot_id == slot.id).order_by(Offer.round, Offer.rank)).all()
    return {
        "id": slot.id,
        "appointment_id": slot.appointment_id,
        "status": slot.status,
        "reason": slot.reason,
        "round": slot.round,
        "radius_multiplier": slot.radius_multiplier,
        "seconds_left": seconds_left(slot),
        "start_time": slot.start_time.isoformat(),
        "time_label": time_label(slot.start_time),
        "offered": [
            {"patient_id": o.patient_id, "name": o.patient.name, "round": o.round, "distance_miles": round(o.distance_miles, 2)}
            for o in offers
        ],
        "booked_by": slot.booked_patient.name if slot.booked_patient else None,
        "booked_patient_id": slot.booked_patient_id,
    }


def _offer_payload(slot: Slot, clinic: Clinic, offer: Offer) -> dict:
    return {
        "slot_id": slot.id,
        "clinic": clinic.name,
        "time_label": time_label(slot.start_time),
        "start_time": slot.start_time.isoformat(),
        "distance_miles": round(offer.distance_miles, 2),
        "round": offer.round,
        "seconds_left": seconds_left(slot),
    }


# ---------- database steps (run in threads) ----------

def _open_slot(appointment_id: int, reason: str) -> dict:
    if reason not in REASON_LABELS:
        raise ServiceError(400, f"Unknown reason '{reason}'.")
    with SessionLocal() as db:
        appt = db.get(Appointment, appointment_id)
        if appt is None:
            raise ServiceError(404, "Appointment not found.")
        # Conditional update: only one request can move it out of 'scheduled'.
        res = db.execute(
            update(Appointment)
            .where(Appointment.id == appointment_id, Appointment.status == "scheduled")
            .values(status=reason)
        )
        if res.rowcount != 1:
            db.rollback()
            raise ServiceError(409, "This appointment was already released.")

        t = now()
        slot = Slot(
            appointment_id=appt.id,
            clinic_id=appt.clinic_id,
            start_time=appt.start_time,
            reason=reason,
            status="open",
            round=0,
            radius_multiplier=1.0,
            opened_at=t,
            expires_at=t + timedelta(seconds=settings.offer_window_seconds),
        )
        db.add(slot)
        db.flush()

        clinic = db.get(Clinic, appt.clinic_id)
        patients = db.scalars(select(Patient)).all()
        matches = rank_candidates(patients, clinic, 1.0)
        offers = []
        for rank, m in enumerate(matches):
            o = Offer(slot_id=slot.id, patient_id=m.patient.id, round=0, rank=rank, distance_miles=m.distance_miles, sent_at=t)
            db.add(o)
            offers.append(o)
        db.commit()

        return {
            "slot": slot_summary(db, slot),
            "offers": [(o.patient_id, _offer_payload(slot, clinic, o)) for o in offers],
            "summary": f"{time_label(slot.start_time)} released ({REASON_LABELS[reason]}). "
            + (f"Offered to {len(offers)} nearby: {', '.join(m.patient.name for m in matches)}" if offers else "Nobody eligible nearby yet; will widen the radius."),
        }


def _expand(slot_id: int, round_no: int) -> dict | None:
    """Widen the radius and offer to newly eligible patients. None if the slot is no longer open."""
    with SessionLocal() as db:
        slot = db.get(Slot, slot_id)
        if slot is None or slot.status != "open":
            return None
        clinic = db.get(Clinic, slot.clinic_id)
        multiplier = settings.radius_growth**round_no
        already = set(db.scalars(select(Offer.patient_id).where(Offer.slot_id == slot_id)).all())
        patients = db.scalars(select(Patient)).all()
        matches = rank_candidates(patients, clinic, multiplier, exclude_ids=already)

        t = now()
        res = db.execute(
            update(Slot)
            .where(Slot.id == slot_id, Slot.status == "open")
            .values(round=round_no, radius_multiplier=multiplier, expires_at=t + timedelta(seconds=settings.offer_window_seconds))
        )
        if res.rowcount != 1:  # claimed in the meantime
            db.rollback()
            return None
        offers = []
        start = len(already)
        for i, m in enumerate(matches):
            o = Offer(slot_id=slot_id, patient_id=m.patient.id, round=round_no, rank=start + i, distance_miles=m.distance_miles, sent_at=t)
            db.add(o)
            offers.append(o)
        db.commit()
        db.refresh(slot)
        return {
            "slot": slot_summary(db, slot),
            "offers": [(o.patient_id, _offer_payload(slot, clinic, o)) for o in offers],
            "still_offered": sorted(already),
            "summary": f"{time_label(slot.start_time)}: no claim yet, radius widened ×{multiplier:g}. "
            + (f"New offers: {', '.join(m.patient.name for m in matches)}" if matches else "No new patients in range."),
        }


def _expire(slot_id: int) -> dict | None:
    with SessionLocal() as db:
        res = db.execute(update(Slot).where(Slot.id == slot_id, Slot.status == "open").values(status="expired"))
        if res.rowcount != 1:
            db.rollback()
            return None
        db.commit()
        slot = db.get(Slot, slot_id)
        offered = list(db.scalars(select(Offer.patient_id).where(Offer.slot_id == slot_id)).all())
        return {
            "slot": slot_summary(db, slot),
            "offered": offered,
            "summary": f"{time_label(slot.start_time)} expired: nobody claimed it.",
        }


def _claim(slot_id: int, patient_id: int) -> dict:
    with SessionLocal() as db:
        slot = db.get(Slot, slot_id)
        if slot is None:
            raise ServiceError(404, "Slot not found.")
        offer = db.scalar(select(Offer).where(Offer.slot_id == slot_id, Offer.patient_id == patient_id))
        if offer is None:
            raise ServiceError(403, "This slot wasn't offered to you.")

        t = now()
        res = db.execute(
            update(Slot)
            .where(Slot.id == slot_id, Slot.status == "open")
            .values(status="booked", booked_patient_id=patient_id, booked_at=t)
        )
        if res.rowcount != 1:
            db.rollback()
            current = db.get(Slot, slot_id)
            db.refresh(current)
            raise ServiceError(409, "Someone else claimed this slot first." if current.status == "booked" else "This offer has expired.")

        # They have their appointment now, so pause their standby.
        db.execute(update(Patient).where(Patient.id == patient_id).values(is_available=False))
        db.commit()
        slot = db.get(Slot, slot_id)
        db.refresh(slot)
        offered = list(db.scalars(select(Offer.patient_id).where(Offer.slot_id == slot_id)).all())
        name = db.get(Patient, patient_id).name
        return {
            "slot": slot_summary(db, slot),
            "offered": offered,
            "winner": patient_id,
            "summary": f"{time_label(slot.start_time)} filled by {name} ({round(offer.distance_miles, 1)} mi away).",
        }


# ---------- async orchestration ----------

async def open_slot(appointment_id: int, reason: str) -> dict:
    result = await asyncio.to_thread(_open_slot, appointment_id, reason)
    slot_id = result["slot"]["id"]
    for patient_id, payload in result["offers"]:
        await broadcaster.to_patient(patient_id, {"type": "offer", "offer": payload})
    await broadcaster.to_clinic({"type": "slot_opened", "slot_id": slot_id, "summary": result["summary"]})
    task = asyncio.create_task(_ripple(slot_id))
    _tasks[slot_id] = task
    # Only remove the registry entry if it still points at this task (slot ids restart after a demo reset).
    task.add_done_callback(lambda t, sid=slot_id: _tasks.pop(sid, None) if _tasks.get(sid) is t else None)
    return result["slot"]


def _current_round(slot_id: int) -> int | None:
    """The slot's current ripple round, or None if it's no longer open."""
    with SessionLocal() as db:
        slot = db.get(Slot, slot_id)
        return slot.round if slot and slot.status == "open" else None


async def _broadcast_expand(result: dict, slot_id: int) -> None:
    for patient_id, payload in result["offers"]:
        await broadcaster.to_patient(patient_id, {"type": "offer", "offer": payload})
    # Patients who already have the offer get a refreshed countdown.
    await broadcaster.to_patients(result["still_offered"], {"type": "offer_extended", "slot_id": slot_id})
    await broadcaster.to_clinic({"type": "slot_updated", "slot_id": slot_id, "summary": result["summary"]})


async def _ripple(slot_id: int) -> None:
    """Wait out each window, then widen. Rounds are read from the slot itself, so a
    manual "increase radius" push (expand_now) advances the same counter and the timer
    simply continues from wherever the slot is now."""
    try:
        while True:
            await asyncio.sleep(settings.offer_window_seconds)
            current = await asyncio.to_thread(_current_round, slot_id)
            if current is None:
                return  # claimed or already expired
            if current >= settings.ripple_rounds:
                break  # no rounds left; fall through to expire
            result = await asyncio.to_thread(_expand, slot_id, current + 1)
            if result is None:
                return
            await _broadcast_expand(result, slot_id)
        result = await asyncio.to_thread(_expire, slot_id)
        if result:
            await broadcaster.to_patients(result["offered"], {"type": "expired", "slot_id": slot_id})
            await broadcaster.to_clinic({"type": "slot_expired", "slot_id": slot_id, "summary": result["summary"]})
    except asyncio.CancelledError:
        pass
    except Exception:  # noqa: BLE001
        log.exception("Ripple task for slot %s failed", slot_id)


async def expand_now(slot_id: int) -> dict:
    """Manually widen the radius right now (nurse pressed "Increase radius"), without
    waiting for the current window. Reuses the same _expand step and then restarts the
    ripple timer so the remaining automatic rounds continue from the new round."""
    current = await asyncio.to_thread(_current_round, slot_id)
    if current is None:
        raise ServiceError(409, "This slot is no longer open.")
    if current >= settings.ripple_rounds:
        raise ServiceError(409, "The radius is already at its widest.")

    # Stop the pending auto-ripple so it doesn't double-expand.
    task = _tasks.pop(slot_id, None)
    if task:
        task.cancel()

    result = await asyncio.to_thread(_expand, slot_id, current + 1)
    if result is None:
        raise ServiceError(409, "This slot is no longer open.")
    await _broadcast_expand(result, slot_id)

    # Restart the ripple timer for whatever rounds remain.
    new_task = asyncio.create_task(_ripple(slot_id))
    _tasks[slot_id] = new_task
    new_task.add_done_callback(lambda t, sid=slot_id: _tasks.pop(sid, None) if _tasks.get(sid) is t else None)
    return result["slot"]


async def claim(slot_id: int, patient_id: int) -> dict:
    result = await asyncio.to_thread(_claim, slot_id, patient_id)
    task = _tasks.pop(slot_id, None)
    if task:
        task.cancel()
    others = [pid for pid in result["offered"] if pid != patient_id]
    await broadcaster.to_patient(patient_id, {"type": "booked", "slot_id": slot_id})
    await broadcaster.to_patients(others, {"type": "taken", "slot_id": slot_id})
    await broadcaster.to_clinic({"type": "slot_booked", "slot_id": slot_id, "summary": result["summary"]})
    return result["slot"]


def cancel_all_tasks() -> None:
    for task in list(_tasks.values()):
        task.cancel()
    _tasks.clear()


def patient_distance(patient: Patient, clinic: Clinic) -> float:
    return haversine_miles(patient.lat, patient.lng, clinic.lat, clinic.lng)
