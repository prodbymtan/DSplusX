"""Slot endpoints: list freed slots, and claim one (first tap wins)."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.db_models import Slot
from app.services import offers
from app.services.offers import ServiceError, slot_summary

router = APIRouter(prefix="/slots", tags=["slots"])


class ClaimRequest(BaseModel):
    patient_id: int


def _list(status: str | None) -> list[dict]:
    with SessionLocal() as db:
        q = select(Slot).order_by(Slot.start_time)
        if status:
            q = q.where(Slot.status == status)
        return [slot_summary(db, s) for s in db.scalars(q).all()]


@router.get("")
async def list_slots(status: str | None = None) -> list[dict]:
    return await asyncio.to_thread(_list, status)


@router.post("/{slot_id}/claim")
async def claim_slot(slot_id: int, body: ClaimRequest) -> dict:
    try:
        return await offers.claim(slot_id, body.patient_id)
    except ServiceError as e:
        raise HTTPException(e.status_code, e.detail) from e
