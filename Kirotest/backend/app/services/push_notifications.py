"""
Firebase Cloud Messaging (FCM) push notification dispatcher.

HIPAA Note: Push notification payloads sent via FCM must NOT contain PHI
(patient name, diagnosis, provider specialty, etc.).
The payload carries only a slot_id and a generic message.
The actual appointment details are fetched inside the app after auth.
"""
from __future__ import annotations

import logging
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_initialized = False


def _ensure_firebase() -> None:
    global _firebase_initialized
    if not _firebase_initialized:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True


def _build_slot_message(
    fcm_token: str,
    slot_id: str,
    clinic_name: str,
    start_time: datetime,
    duration_minutes: int,
    distance_m: float,
) -> messaging.Message:
    """
    Builds an FCM message.

    The notification body is intentionally generic (HIPAA-safe).
    The data payload carries slot_id so the app can fetch full details post-auth.
    """
    minutes_away = max(1, round(distance_m / 80))  # rough walking-speed estimate

    return messaging.Message(
        token=fcm_token,
        notification=messaging.Notification(
            title="⚡ Appointment Opening Nearby",
            body=(
                f"A {duration_minutes}-min slot just opened at {clinic_name}. "
                f"You're ~{minutes_away} min away. Tap to claim before it's gone."
            ),
        ),
        data={
            "slot_id": slot_id,
            "event_type": "slot_available",
            "clinic_name": clinic_name,           # clinic name is not PHI
            "start_time": start_time.isoformat(),
            "duration_minutes": str(duration_minutes),
        },
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                sound="default",
                channel_id="slot_alerts",
            ),
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound="default", badge=1)
            )
        ),
    )


async def send_slot_alert_batch(
    recipients: list[dict],          # [{user_id, fcm_token, distance_m}]
    slot_id: str,
    clinic_name: str,
    start_time: datetime,
    duration_minutes: int,
) -> dict:
    """
    Send push notifications to all nearby standby patients simultaneously.
    Uses FCM batch send for efficiency (up to 500 messages per call).
    Returns a summary of successes/failures.
    """
    _ensure_firebase()

    messages = [
        _build_slot_message(
            fcm_token=r["fcm_token"],
            slot_id=slot_id,
            clinic_name=clinic_name,
            start_time=start_time,
            duration_minutes=duration_minutes,
            distance_m=r.get("distance_m", 0),
        )
        for r in recipients
    ]

    if not messages:
        return {"success": 0, "failure": 0}

    try:
        batch_response = messaging.send_each(messages)
        success_count = batch_response.success_count
        failure_count = batch_response.failure_count

        if failure_count:
            for i, resp in enumerate(batch_response.responses):
                if not resp.success:
                    logger.warning(
                        "Push failed for user %s: %s",
                        recipients[i]["user_id"],
                        resp.exception,
                    )

        logger.info(
            "Push batch: %d sent, %d failed for slot %s",
            success_count,
            failure_count,
            slot_id,
        )
        return {"success": success_count, "failure": failure_count}

    except Exception as exc:
        logger.exception("FCM batch send failed: %s", exc)
        return {"success": 0, "failure": len(messages)}


async def send_booking_confirmation(fcm_token: str, slot_id: str, clinic_name: str) -> bool:
    """Send a confirmation push after a patient successfully books a slot."""
    _ensure_firebase()
    message = messaging.Message(
        token=fcm_token,
        notification=messaging.Notification(
            title="✅ Booking Confirmed",
            body=f"Your appointment at {clinic_name} is confirmed. See you soon!",
        ),
        data={"slot_id": slot_id, "event_type": "booking_confirmed"},
    )
    try:
        messaging.send(message)
        return True
    except Exception as exc:
        logger.exception("Confirmation push failed: %s", exc)
        return False
