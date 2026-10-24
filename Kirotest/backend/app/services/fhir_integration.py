"""
FHIR / EHR Integration Service
────────────────────────────────
Listens for appointment status webhooks from Epic/Cerner/Athena
and translates them into internal slot state changes.

FHIR R4 resources used:
  - Appointment     → maps to AppointmentSlot
  - Organization    → maps to Clinic
  - Practitioner    → maps to Provider

Webhook flow (Epic example):
  1. Epic fires a FHIR Subscription notification to POST /api/v1/webhooks/fhir
  2. This service parses the Bundle, extracts the Appointment resource
  3. Maps FHIR status → internal SlotStatus
  4. Updates the DB and triggers the matching engine broadcast if needed
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slot import AppointmentSlot
from app.services.matching_engine import trigger_slot_broadcast

logger = logging.getLogger(__name__)

# FHIR Appointment.status → internal SlotStatus mapping
FHIR_STATUS_MAP: dict[str, str] = {
    "proposed": "available",
    "pending": "available",
    "booked": "booked",
    "arrived": "booked",
    "fulfilled": "completed",
    "cancelled": "available",      # cancellation → re-open the slot
    "noshow": "no_show",
    "entered-in-error": "cancelled",
    "checked-in": "booked",
    "waitlist": "available",
}


async def handle_fhir_appointment_event(
    fhir_bundle: dict,
    db: AsyncSession,
) -> dict:
    """
    Parse a FHIR R4 Bundle notification and apply state changes.

    Expected bundle structure (simplified):
    {
      "resourceType": "Bundle",
      "entry": [{
        "resource": {
          "resourceType": "Appointment",
          "id": "<ehr_slot_id>",
          "status": "cancelled" | "noshow" | ...,
          "start": "<ISO8601>",
          ...
        }
      }]
    }
    """
    results = []
    entries = fhir_bundle.get("entry", [])

    for entry in entries:
        resource = entry.get("resource", {})
        if resource.get("resourceType") != "Appointment":
            continue

        ehr_slot_id = resource.get("id")
        fhir_status = resource.get("status", "")
        internal_status = FHIR_STATUS_MAP.get(fhir_status)

        if not ehr_slot_id or not internal_status:
            logger.warning("Unrecognised FHIR status '%s' for slot %s", fhir_status, ehr_slot_id)
            continue

        # Find the slot by EHR ID
        result = await db.execute(
            select(AppointmentSlot).where(AppointmentSlot.ehr_slot_id == ehr_slot_id)
        )
        slot = result.scalar_one_or_none()

        if not slot:
            logger.info("No local slot found for EHR ID %s — skipping", ehr_slot_id)
            results.append({"ehr_slot_id": ehr_slot_id, "action": "not_found"})
            continue

        previous_status = slot.status
        slot.status = internal_status

        # If the slot just became available, trigger the broadcast engine
        if internal_status == "available" and previous_status in ("booked", "locked"):
            await db.flush()   # persist status before broadcasting
            await trigger_slot_broadcast(slot_id=slot.id, db=db)
            action = "broadcast_triggered"
        elif internal_status == "no_show":
            # No-show: re-open the slot and broadcast
            slot.status = "available"
            await db.flush()
            await trigger_slot_broadcast(slot_id=slot.id, db=db)
            action = "no_show_broadcast_triggered"
        else:
            action = f"status_updated_to_{internal_status}"

        results.append(
            {
                "ehr_slot_id": ehr_slot_id,
                "slot_id": str(slot.id),
                "previous_status": previous_status,
                "new_status": slot.status,
                "action": action,
            }
        )
        logger.info(
            "FHIR event processed: %s %s → %s (%s)",
            ehr_slot_id,
            previous_status,
            slot.status,
            action,
        )

    return {"processed": len(results), "results": results}


def parse_fhir_datetime(fhir_dt: str) -> datetime:
    """Parse FHIR ISO8601 datetime string to timezone-aware Python datetime."""
    return datetime.fromisoformat(fhir_dt.replace("Z", "+00:00")).astimezone(timezone.utc)
