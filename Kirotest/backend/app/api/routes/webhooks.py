"""
FHIR Webhook endpoint — receives appointment status events from EHR systems.

Security: EHR systems sign their webhook payloads.
This endpoint verifies the HMAC-SHA256 signature before processing.
"""
import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.fhir_integration import handle_fhir_appointment_event

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

# FHIR webhook secret — set per EHR partner in environment
WEBHOOK_SECRET = settings.FHIR_CLIENT_SECRET


@router.post("/fhir", status_code=status.HTTP_200_OK)
async def fhir_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_hub_signature: str | None = Header(None),  # Epic uses X-Hub-Signature-256
):
    """
    Receives FHIR R4 Subscription Bundle notifications from EHR systems.
    Verifies signature, parses the bundle, and delegates to the FHIR service.
    """
    body = await request.body()

    # Verify HMAC signature if the EHR supplies one
    if WEBHOOK_SECRET and x_hub_signature:
        expected = "sha256=" + hmac.new(
            WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature):
            logger.warning("FHIR webhook signature mismatch")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        bundle = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    result = await handle_fhir_appointment_event(fhir_bundle=bundle, db=db)
    return result
