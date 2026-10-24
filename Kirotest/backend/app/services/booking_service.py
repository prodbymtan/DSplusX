"""
Booking Service
────────────────
Handles the atomic claim-and-book flow with distributed locking via Redis
to prevent double-booking race conditions when multiple patients tap
"Claim" simultaneously.

Race condition prevention flow:
  1. Patient taps "Claim" → POST /api/v1/bookings/claim
  2. Service attempts Redis SET NX (atomic, 30-second TTL)
  3. If lock acquired → update slot status to "locked" in DB
  4. Patient sees 30-second countdown to confirm
  5. Patient confirms → slot status → "booked", Booking record created
  6. If patient doesn't confirm within TTL → Celery task releases lock + re-broadcasts
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import (
    acquire_slot_lock,
    get_slot_lock_owner,
    release_slot_lock,
)
from app.models.booking import Booking
from app.models.slot import AppointmentSlot
from app.models.user import User
from app.services.push_notifications import send_booking_confirmation

logger = logging.getLogger(__name__)


class BookingError(Exception):
    pass


async def claim_slot(slot_id: UUID, patient_id: UUID, db: AsyncSession) -> dict:
    """
    Step 1: Attempt to acquire a distributed lock on the slot.
    Returns a "pending" booking token on success.
    Raises BookingError if the slot is unavailable or already locked.
    """
    # Verify slot exists and is available
    result = await db.execute(
        select(AppointmentSlot).where(AppointmentSlot.id == slot_id)
    )
    slot = result.scalar_one_or_none()

    if not slot:
        raise BookingError("Slot not found")
    if slot.status != "available":
        raise BookingError(f"Slot is not available (current status: {slot.status})")

    # Acquire distributed Redis lock (atomic SET NX)
    acquired = await acquire_slot_lock(str(slot_id), str(patient_id))
    if not acquired:
        # Check if this patient already holds the lock
        owner = await get_slot_lock_owner(str(slot_id))
        if owner == str(patient_id):
            # Idempotent: patient re-tapped, return existing pending state
            return {
                "status": "pending",
                "slot_id": str(slot_id),
                "message": "You already have this slot held. Please confirm.",
            }
        raise BookingError("This slot was just claimed by another patient")

    # Mark slot as locked in DB
    slot.status = "locked"
    await db.flush()

    logger.info("Slot %s locked by patient %s", slot_id, patient_id)
    return {
        "status": "pending",
        "slot_id": str(slot_id),
        "expires_in_seconds": 30,
        "message": "Slot held for 30 seconds. Confirm now to secure your booking.",
    }


async def confirm_booking(
    slot_id: UUID,
    patient_id: UUID,
    notes: str | None,
    db: AsyncSession,
) -> Booking:
    """
    Step 2: Patient confirms within the 30-second window.
    Creates a Booking record, updates slot to "booked", releases the Redis lock.
    """
    # Verify this patient holds the lock
    owner = await get_slot_lock_owner(str(slot_id))
    if owner != str(patient_id):
        raise BookingError("Your hold on this slot has expired. Please try again.")

    result = await db.execute(
        select(AppointmentSlot).where(AppointmentSlot.id == slot_id)
    )
    slot = result.scalar_one_or_none()
    if not slot or slot.status != "locked":
        raise BookingError("Slot is no longer available for confirmation")

    # Create booking record
    booking = Booking(
        slot_id=slot_id,
        patient_id=patient_id,
        status="confirmed",
        notes=notes,
    )
    db.add(booking)
    slot.status = "booked"

    # Release the Redis lock
    await release_slot_lock(str(slot_id))
    await db.flush()

    # Send confirmation push (best-effort, don't fail booking if push fails)
    patient_result = await db.execute(select(User).where(User.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if patient and patient.fcm_token:
        try:
            await send_booking_confirmation(
                fcm_token=patient.fcm_token,
                slot_id=str(slot_id),
                clinic_name=slot.clinic.name if slot.clinic else "the clinic",
            )
        except Exception:
            logger.warning("Confirmation push failed for patient %s", patient_id)

    logger.info("Booking confirmed: slot %s → patient %s", slot_id, patient_id)
    return booking


async def release_expired_lock(slot_id: UUID, db: AsyncSession) -> None:
    """
    Called by a Celery task when the 30-second claim window expires without confirmation.
    Releases the lock and re-opens the slot for other patients.
    """
    # Only release if the lock is still set (patient may have already confirmed)
    owner = await get_slot_lock_owner(str(slot_id))
    if not owner:
        return  # already released or confirmed

    await release_slot_lock(str(slot_id))

    result = await db.execute(
        select(AppointmentSlot).where(AppointmentSlot.id == slot_id)
    )
    slot = result.scalar_one_or_none()
    if slot and slot.status == "locked":
        slot.status = "available"
        await db.flush()
        logger.info("Lock expired: slot %s re-opened", slot_id)

        # Re-trigger broadcast for next nearest patient
        from app.services.matching_engine import trigger_slot_broadcast
        await trigger_slot_broadcast(slot_id=slot_id, db=db)
