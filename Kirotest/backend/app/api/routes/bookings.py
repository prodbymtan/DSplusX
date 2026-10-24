"""
Booking endpoints:
  POST /bookings/claim    — patient atomically claims a slot (acquires Redis lock)
  POST /bookings/confirm  — patient confirms within 30-second window
  GET  /bookings/my       — patient's booking history
  POST /bookings/{id}/cancel — patient cancels a booking
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.booking import Booking
from app.models.slot import AppointmentSlot
from app.models.user import User
from app.schemas.slot import BookingClaim
from app.services.booking_service import BookingError, claim_slot, confirm_booking
from app.services.matching_engine import trigger_slot_broadcast

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/claim")
async def claim(
    payload: BookingClaim,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Atomically claim a slot.  Returns a 30-second hold token.
    First caller wins — all subsequent callers receive 409 Conflict.
    """
    try:
        result = await claim_slot(
            slot_id=payload.slot_id,
            patient_id=current_user.id,
            db=db,
        )
        return result
    except BookingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/confirm")
async def confirm(
    payload: BookingClaim,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a previously claimed slot within the 30-second window."""
    try:
        booking = await confirm_booking(
            slot_id=payload.slot_id,
            patient_id=current_user.id,
            notes=payload.notes,
            db=db,
        )
        return {
            "booking_id": str(booking.id),
            "slot_id": str(booking.slot_id),
            "status": booking.status,
            "confirmed_at": booking.confirmed_at.isoformat(),
        }
    except BookingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/my", response_model=list[dict])
async def my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated patient's full booking history."""
    result = await db.execute(
        select(Booking)
        .where(Booking.patient_id == current_user.id)
        .order_by(Booking.confirmed_at.desc())
    )
    bookings = result.scalars().all()
    return [
        {
            "booking_id": str(b.id),
            "slot_id": str(b.slot_id),
            "status": b.status,
            "notes": b.notes,
            "confirmed_at": b.confirmed_at.isoformat(),
        }
        for b in bookings
    ]


@router.post("/{booking_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Patient cancels their own booking — slot is immediately re-broadcast."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if str(booking.patient_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your booking")
    if booking.status != "confirmed":
        raise HTTPException(status_code=400, detail=f"Cannot cancel a '{booking.status}' booking")

    booking.status = "cancelled_by_patient"

    # Re-open the slot and broadcast to standby patients
    slot_result = await db.execute(
        select(AppointmentSlot).where(AppointmentSlot.id == booking.slot_id)
    )
    slot = slot_result.scalar_one_or_none()
    if slot:
        slot.status = "available"
        await db.flush()
        await trigger_slot_broadcast(slot_id=slot.id, db=db)

    return {"message": "Booking cancelled. Slot re-opened for other patients."}
