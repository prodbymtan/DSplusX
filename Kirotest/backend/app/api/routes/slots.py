"""
Slot endpoints:
  - GET  /slots/nearby   — find available slots near patient's current location
  - POST /slots          — clinic staff creates a new slot
  - POST /slots/{id}/status — clinic staff updates slot status (triggers broadcast)
  - POST /standby/activate  — patient activates standby mode
  - POST /standby/deactivate — patient deactivates standby mode
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_clinic_staff
from app.core.database import get_db
from app.core.redis_client import remove_standby, set_standby
from app.models.slot import AppointmentSlot
from app.models.user import User
from app.schemas.slot import SlotCreate, SlotRead, SlotStatusUpdate, StandbyActivate
from app.services.matching_engine import trigger_slot_broadcast

router = APIRouter(prefix="/slots", tags=["slots"])


@router.get("/nearby", response_model=list[SlotRead])
async def get_nearby_slots(
    lat: float = Query(..., ge=-90, le=90, description="Patient latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Patient longitude"),
    radius_meters: int = Query(5000, ge=500, le=25_000),
    appointment_type: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns available slots within radius of the patient's current location.
    Uses PostGIS ST_DWithin for efficient spatial filtering.
    Results include distance_meters for client-side display.
    """
    type_filter = ""
    params: dict = {"lat": lat, "lng": lng, "radius": radius_meters}
    if appointment_type:
        type_filter = "AND s.appointment_type = :appt_type"
        params["appt_type"] = appointment_type

    query = text(f"""
        SELECT
            s.id,
            s.clinic_id,
            s.provider_id,
            s.start_time,
            s.end_time,
            s.duration_minutes,
            s.appointment_type,
            s.status,
            p.full_name  AS provider_name,
            c.name       AS clinic_name,
            ST_Distance(
                c.location::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            ) AS distance_meters
        FROM appointment_slots s
        JOIN clinics   c ON c.id = s.clinic_id
        JOIN providers p ON p.id = s.provider_id
        WHERE s.status = 'available'
          AND s.start_time > NOW()
          AND ST_DWithin(
              c.location::geography,
              ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
              :radius
          )
          {type_filter}
        ORDER BY distance_meters, s.start_time
        LIMIT 50
    """)

    result = await db.execute(query, params)
    rows = result.mappings().all()
    return [SlotRead(**dict(row)) for row in rows]


@router.post("", response_model=SlotRead, status_code=status.HTTP_201_CREATED)
async def create_slot(
    payload: SlotCreate,
    current_user: User = Depends(require_clinic_staff),
    db: AsyncSession = Depends(get_db),
):
    """Clinic staff creates a new appointment slot."""
    from datetime import timezone

    duration = int((payload.end_time - payload.start_time).total_seconds() / 60)
    slot = AppointmentSlot(
        clinic_id=payload.clinic_id,
        provider_id=payload.provider_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        duration_minutes=duration,
        appointment_type=payload.appointment_type,
        status="available",
    )
    db.add(slot)
    await db.flush()
    return slot


@router.patch("/{slot_id}/status", response_model=SlotRead)
async def update_slot_status(
    slot_id: UUID,
    payload: SlotStatusUpdate,
    current_user: User = Depends(require_clinic_staff),
    db: AsyncSession = Depends(get_db),
):
    """
    Clinic staff manually updates a slot status.
    If set to 'available', triggers the standby broadcast engine.
    """
    result = await db.execute(select(AppointmentSlot).where(AppointmentSlot.id == slot_id))
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    allowed_transitions = {
        "available": ["cancelled"],
        "locked": ["available"],        # admin override
        "booked": ["no_show", "completed", "cancelled_by_clinic"],
        "no_show": [],
        "completed": [],
        "cancelled": [],
    }
    if payload.status not in allowed_transitions.get(slot.status, []):
        # Special case: explicitly setting to available (e.g. after cancellation)
        if payload.status != "available":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from '{slot.status}' to '{payload.status}'",
            )

    slot.status = payload.status
    await db.flush()

    # Broadcast if reopening
    if payload.status == "available":
        await trigger_slot_broadcast(slot_id=slot_id, db=db)

    return slot


# ── Standby endpoints ────────────────────────────────────────────────────────

standby_router = APIRouter(prefix="/standby", tags=["standby"])


@standby_router.post("/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_standby(
    payload: StandbyActivate,
    current_user: User = Depends(get_current_user),
):
    """
    Patient declares they are in standby mode at a given location.
    Stores location in Redis with a TTL — no continuous tracking.
    """
    await set_standby(
        user_id=str(current_user.id),
        lat=payload.lat,
        lng=payload.lng,
        ttl=payload.duration_seconds,
    )


@standby_router.post("/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_standby(current_user: User = Depends(get_current_user)):
    """Patient explicitly goes offline from standby mode."""
    await remove_standby(user_id=str(current_user.id))
