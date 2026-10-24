"""Keeps track of open WebSocket connections and pushes messages to them.

Two audiences: the clinic dashboard, and each patient's phone.
Messages are hints; the frontend re-fetches state over REST after each one,
so a dropped message never leaves a screen wrong for long.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket

log = logging.getLogger(__name__)


class Broadcaster:
    def __init__(self) -> None:
        self.clinic: set[WebSocket] = set()
        self.patients: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect_clinic(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clinic.add(ws)

    async def connect_patient(self, patient_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self.patients[patient_id].add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.clinic.discard(ws)
        for conns in self.patients.values():
            conns.discard(ws)

    async def _send(self, targets: set[WebSocket], message: dict) -> None:
        dead = []
        for ws in list(targets):
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001  (client went away)
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def to_clinic(self, message: dict) -> None:
        await self._send(self.clinic, message)

    async def to_patient(self, patient_id: int, message: dict) -> None:
        await self._send(self.patients.get(patient_id, set()), message)

    async def to_patients(self, patient_ids: list[int], message: dict) -> None:
        await asyncio.gather(*(self.to_patient(pid, message) for pid in patient_ids))

    async def to_everyone(self, message: dict) -> None:
        await self.to_clinic(message)
        await asyncio.gather(*(self.to_patient(pid, message) for pid in list(self.patients)))


broadcaster = Broadcaster()
