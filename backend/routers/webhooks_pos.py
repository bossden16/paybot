"""
Webhook handlers for Magpie payment status callbacks.
"""
import json
import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.database import get_db
from services.pos_terminal import POSTerminalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


@router.get("/magpie/payment-status")
async def magpie_payment_webhook_verify():
    """Verify endpoint is reachable via GET."""
    return {"status": "active", "message": "Magpie webhook endpoint is ready for POST requests"}


@router.post("/magpie/payment-status")
async def magpie_payment_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Webhook endpoint for Magpie payment status updates."""
    try:
        body = await request.body()
        payload = json.loads(body)
        logger.info("Magpie webhook received: %s", payload)

        checkout_id = payload.get("id") or payload.get("checkoutId")
        status = str(payload.get("status", "")).upper()
        request_reference = payload.get("requestReferenceNumber") or payload.get("reference")

        if not request_reference:
            logger.warning("No request reference in Magpie webhook")
            return {"success": True, "message": "Webhook received"}

        service = POSTerminalService(db)

        status_map = {
            "COMPLETED": "completed",
            "SUCCESS": "completed",
            "AUTHORIZED": "completed",
            "PENDING": "pending",
            "FAILED": "failed",
            "CANCELLED": "cancelled",
            "EXPIRED": "failed",
        }

        transaction_status = status_map.get(status, "pending")
        failure_reason = None
        if status in ["FAILED", "EXPIRED", "CANCELLED"]:
            failure_reason = payload.get("failureReason") or payload.get("message") or f"Payment {status}"

        result = await service.update_transaction_status(
            order_id=request_reference,
            status=transaction_status,
            failure_reason=failure_reason,
        )

        if result.get("success"):
            logger.info(
                "Transaction %s updated with status %s (checkout=%s)",
                request_reference,
                transaction_status,
                checkout_id,
            )
        else:
            logger.warning("Failed to update transaction %s: %s", request_reference, result.get("error"))

        # Always return success to avoid provider retries while keeping logs for diagnostics.
        return {"success": True, "message": "Webhook processed"}

    except Exception as exc:
        logger.error("Error processing Magpie webhook: %s", exc)
        return {"success": True, "message": "Webhook received"}


@router.post("/test")
async def test_webhook(request: Request):
    """Test webhook endpoint."""
    body = await request.body()
    payload = json.loads(body)
    logger.info("Test webhook received: %s", payload)
    return {"success": True, "received": payload}
