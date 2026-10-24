"""
WebSocket endpoint for real-time slot event streaming.

Patients connected via WebSocket receive instant slot_available events
without needing to poll the REST API.

Flow:
  1. Client connects: ws://server/api/v1/ws?token=<JWT>
  2. Server verifies JWT and subscribes to Redis pub/sub channel
  3. When a slot opens, matching_engine publishes to Redis
  4. This handler forwards the event to all connected WebSocket clients
  5. Client-side can filter by distance/preference before showing UI alert
"""
import asyncio
import json
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.core.config import settings
from app.core.redis_client import SLOT_CHANNEL, get_redis
from app.core.security import decode_access_token

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def slot_events_ws(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    Real-time WebSocket feed of slot availability events.
    Requires a valid JWT passed as a query parameter.
    """
    # Verify JWT before accepting connection
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except JWTError:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()
    logger.info("WebSocket connected: user %s", user_id)

    # Subscribe to Redis pub/sub channel
    r: aioredis.Redis = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(SLOT_CHANNEL)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    event = json.loads(message["data"])
                    await websocket.send_json(event)
                except (json.JSONDecodeError, Exception) as exc:
                    logger.warning("WS send error for user %s: %s", user_id, exc)
                    break
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: user %s", user_id)
    except Exception as exc:
        logger.exception("WebSocket error for user %s: %s", user_id, exc)
    finally:
        await pubsub.unsubscribe(SLOT_CHANNEL)
        await pubsub.aclose()
