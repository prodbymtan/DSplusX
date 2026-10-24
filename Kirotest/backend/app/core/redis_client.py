"""
Shared async Redis client used for:
  - Distributed booking locks (preventing double-booking race conditions)
  - Standby session tracking (who is currently online and nearby)
  - Pub/sub for real-time slot-open broadcasts to WebSocket connections
"""
import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


# ── Distributed lock helpers ─────────────────────────────────────────────────

LOCK_PREFIX = "slot_lock:"


async def acquire_slot_lock(slot_id: str, user_id: str) -> bool:
    """
    Atomically set a lock key only if it doesn't already exist (NX).
    Returns True if this caller acquired the lock, False if already locked.
    """
    r = await get_redis()
    key = f"{LOCK_PREFIX}{slot_id}"
    result = await r.set(key, user_id, nx=True, ex=settings.BOOKING_LOCK_TTL_SECONDS)
    return result is True


async def release_slot_lock(slot_id: str) -> None:
    r = await get_redis()
    await r.delete(f"{LOCK_PREFIX}{slot_id}")


async def get_slot_lock_owner(slot_id: str) -> str | None:
    r = await get_redis()
    return await r.get(f"{LOCK_PREFIX}{slot_id}")


# ── Standby session helpers ──────────────────────────────────────────────────

STANDBY_PREFIX = "standby:"


async def set_standby(user_id: str, lat: float, lng: float, ttl: int = 7200) -> None:
    """Store a patient's standby location with a TTL (default 2 h)."""
    r = await get_redis()
    payload = json.dumps({"lat": lat, "lng": lng})
    await r.set(f"{STANDBY_PREFIX}{user_id}", payload, ex=ttl)


async def remove_standby(user_id: str) -> None:
    r = await get_redis()
    await r.delete(f"{STANDBY_PREFIX}{user_id}")


async def get_all_standby_users() -> dict[str, dict]:
    """Return {user_id: {lat, lng}} for every patient currently on standby."""
    r = await get_redis()
    keys = await r.keys(f"{STANDBY_PREFIX}*")
    if not keys:
        return {}
    values = await r.mget(*keys)
    result = {}
    for key, value in zip(keys, values):
        if value:
            user_id = key.removeprefix(STANDBY_PREFIX)
            result[user_id] = json.loads(value)
    return result


# ── Pub/Sub channel helpers ──────────────────────────────────────────────────

SLOT_CHANNEL = "slot_events"


async def publish_slot_event(event: dict) -> None:
    """Broadcast a slot-open or slot-filled event to all WebSocket listeners."""
    r = await get_redis()
    await r.publish(SLOT_CHANNEL, json.dumps(event))
