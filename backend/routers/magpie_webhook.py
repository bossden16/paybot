import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, Header, HTTPException, status

from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/magpie", tags=["magpie"])


@router.post("/webhook")
async def magpie_webhook(request: Request, x_magpie_signature: str | None = Header(None)):
    """Receive Magpie webhook notifications and verify HMAC signature.

    The webhook secret should be set in `MAGPIE_WEBHOOK_SECRET`.
    If not configured, the handler will accept the request but log a warning.
    """
    body = await request.body()
    # Verify signature if secret is configured
    secret = getattr(settings, "magpie_webhook_secret", "") or ""
    if secret:
        if not x_magpie_signature:
            logger.warning("Magpie webhook received without signature header")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature")
        try:
            computed = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        except Exception as e:
            logger.exception("Failed to compute HMAC for Magpie webhook: %s", e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Signature verification error")
        if not hmac.compare_digest(computed, x_magpie_signature):
            logger.warning("Magpie webhook signature mismatch: expected=%s received=%s", computed, x_magpie_signature)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    else:
        logger.warning("MAGPIE_WEBHOOK_SECRET not set — skipping signature verification (only for testing)")

    try:
        payload = await request.json()
    except Exception:
        logger.exception("Magpie webhook: failed to parse JSON payload")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    # Basic routing based on event type / resource
    event_type = payload.get("event") or payload.get("type") or payload.get("event_type")
    logger.info("Magpie webhook received: event=%s payload=%s", event_type, payload)

    # TODO: dispatch to internal handlers (payments, refunds, payouts) and acknowledge
    return {"success": True}
