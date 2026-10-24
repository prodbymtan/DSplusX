"""
Geospatial Matching Engine
───────────────────────────
When a slot opens (cancellation or no-show trigger), this engine:
  1. Fetches all patients currently in standby mode from Redis
  2. Filters those within the configured radius of the clinic (PostGIS ST_DWithin)
  3. Ranks them by proximity (closest first)
  4. Broadcasts a push notification to the top N candidates simultaneously
  5. The first patient to claim via the API wins the distributed lock
"""
from __future__ import annotations

import logging
import math
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis_client import get_all_standby_users, publish_slot_event
from app.models.clinic import Clinic
from app.models.slot import AppointmentSlot
from app.services.push_notifications import send_slot_alert_batch

logger = logging.getLogger(__name__)

# How many standby patients to notify simultaneously (Uber-style broadcast)
BROADCAST_LIMIT = 10


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance between two points in metres.
    Used for in-memory filtering after the PostGIS query narrows candidates.
    """
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def find_nearby_standby_patients(
    clinic_lat: float,
    clinic_lng: float,
    radius_meters: int = settings.DEFAULT_STANDBY_RADIUS_METERS,
) -> list[dict]:
    """
    Pull all standby users from Redis, compute distance to clinic,
    and return those within radius sorted by proximity (closest first).

    Returns list of: {"user_id": str, "lat": float, "lng": float, "distance_m": float}
    """
    standby_users = await get_all_standby_users()
    if not standby_users:
        return []

    nearby: list[dict] = []
    for user_id, coords in standby_users.items():
        distance = _haversine_meters(
            clinic_lat, clinic_lng, coords["lat"], coords["lng"]
        )
        if distance <= radius_meters:
            nearby.append(
                {
                    "user_id": user_id,
                    "lat": coords["lat"],
                    "lng": coords["lng"],
                    "distance_m": round(distance, 1),
                }
            )

    nearby.sort(key=lambda x: x["distance_m"])
    return nearby[:BROADCAST_LIMIT]


async def trigger_slot_broadcast(
    slot_id: UUID,
    db: AsyncSession,
) -> int:
    """
    Main entry point called when a slot becomes available (cancellation / no-show).

    Steps:
      1. Load slot + clinic from DB
      2. Get nearby standby patients
      3. Load their FCM tokens from DB
      4. Send push notifications
      5. Publish Redis event for WebSocket listeners
      6. Return count of notified patients
    """
    # 1. Load slot and clinic
    result = await db.execute(
        select(AppointmentSlot).where(AppointmentSlot.id == slot_id)
    )
    slot = result.scalar_one_or_none()
    if not slot or slot.status != "available":
        logger.warning("Broadcast skipped: slot %s not available", slot_id)
        return 0

    clinic_result = await db.execute(
        select(Clinic).where(Clinic.id == slot.clinic_id)
    )
    clinic = clinic_result.scalar_one_or_none()
    if not clinic:
        return 0

    # Extract lat/lng from PostGIS POINT geometry using ST_X / ST_Y
    geo_result = await db.execute(
        text(
            "SELECT ST_X(location::geometry) AS lng, ST_Y(location::geometry) AS lat "
            "FROM clinics WHERE id = :cid"
        ),
        {"cid": str(clinic.id)},
    )
    geo_row = geo_result.fetchone()
    if not geo_row:
        return 0
    clinic_lat, clinic_lng = geo_row.lat, geo_row.lng

    # 2. Find nearby standby patients
    nearby = await find_nearby_standby_patients(clinic_lat, clinic_lng)
    if not nearby:
        logger.info("No standby patients found near clinic %s", clinic.id)
        return 0

    # 3. Fetch FCM tokens for these users
    user_ids = [p["user_id"] for p in nearby]
    from app.models.user import User  # local import to avoid circular
    token_result = await db.execute(
        select(User.id, User.fcm_token).where(
            User.id.in_(user_ids),
            User.fcm_token.is_not(None),
        )
    )
    token_map = {str(row.id): row.fcm_token for row in token_result.fetchall()}

    # 4. Send push notifications
    recipients = [
        {"user_id": p["user_id"], "fcm_token": token_map[p["user_id"]], "distance_m": p["distance_m"]}
        for p in nearby
        if p["user_id"] in token_map
    ]

    if recipients:
        await send_slot_alert_batch(
            recipients=recipients,
            slot_id=str(slot_id),
            clinic_name=clinic.name,
            start_time=slot.start_time,
            duration_minutes=slot.duration_minutes,
        )

    # 5. Publish Redis event for WebSocket listeners
    await publish_slot_event(
        {
            "event": "slot_available",
            "slot_id": str(slot_id),
            "clinic_id": str(clinic.id),
            "clinic_name": clinic.name,
            "start_time": slot.start_time.isoformat(),
            "duration_minutes": slot.duration_minutes,
            "notified_count": len(recipients),
        }
    )

    logger.info(
        "Broadcast complete: slot %s → %d patients notified", slot_id, len(recipients)
    )
    return len(recipients)
