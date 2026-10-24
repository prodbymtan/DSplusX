"""WebSocket endpoints. Clients just listen; all actions go through REST."""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.broadcaster import broadcaster

router = APIRouter()


async def _hold(ws: WebSocket) -> None:
    """Keep the socket open; reply to pings so clients can detect dead connections."""
    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.disconnect(ws)


@router.websocket("/ws/clinic")
async def clinic_socket(ws: WebSocket) -> None:
    await broadcaster.connect_clinic(ws)
    await ws.send_json({"type": "hello", "role": "clinic"})
    await _hold(ws)


@router.websocket("/ws/patients/{patient_id}")
async def patient_socket(ws: WebSocket, patient_id: int) -> None:
    await broadcaster.connect_patient(patient_id, ws)
    await ws.send_json({"type": "hello", "role": "patient", "patient_id": patient_id})
    await _hold(ws)
