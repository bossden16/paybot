"""Legacy Magpie route compatibility layer.

Keeps old /api/v1/magpie endpoints working by forwarding to the xend router logic.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
import uuid
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_payment_user
from schemas.auth import UserResponse
from services.magpie_service import MagpieService
from services.transactions import TransactionsService
from . import xend

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/magpie", tags=["magpie-legacy"])


class CheckoutSessionRequest(BaseModel):
    payment_method_types: List[str] = Field(default_factory=list)
    payment_methods: List[str] = Field(default_factory=list)
    line_items: Optional[List[Dict[str, Any]]] = None
    mode: str = "payment"
    success_url: str = ""
    cancel_url: str = ""
    currency: str = "php"
    customer_email: str = ""
    external_id: str = ""
    amount: Optional[float] = None
    description: str = ""
    metadata: Optional[Dict[str, Any]] = None


@router.get("/payment-methods")
async def get_supported_payment_methods():
    return await xend.get_supported_payment_methods()


@router.get("/transaction-stats")
async def get_transaction_stats(
    current_user: UserResponse = Depends(get_payment_user("payments:read")),
    db: AsyncSession = Depends(get_db),
):
    return await xend.get_transaction_stats(current_user=current_user, db=db)


@router.post("/create-invoice")
async def create_invoice(
    data: xend.CreatePaymentRequest,
    current_user: UserResponse = Depends(get_payment_user("payments:write")),
    db: AsyncSession = Depends(get_db),
):
    return await xend.create_invoice(data=data, current_user=current_user, db=db)


@router.post("/create-payment-link")
async def create_payment_link(
    data: xend.CreatePaymentRequest,
    current_user: UserResponse = Depends(get_payment_user("payments:write")),
    db: AsyncSession = Depends(get_db),
):
    return await xend.create_payment_link(data=data, current_user=current_user, db=db)


@router.post("/create-qr-code")
async def create_qr_code(
    data: xend.CreatePaymentRequest,
    current_user: UserResponse = Depends(get_payment_user("payments:write")),
    db: AsyncSession = Depends(get_db),
):
    return await xend.create_qr_code(data=data, current_user=current_user, db=db)


@router.post("/pay-qrph")
async def pay_qrph(
    data: xend.PayQRPhRequest,
    current_user: UserResponse = Depends(get_payment_user("payments:write")),
    db: AsyncSession = Depends(get_db),
):
    return await xend.pay_qrph(data=data, current_user=current_user, db=db)


@router.post("/checkout/sessions")
async def create_checkout_session(
    data: CheckoutSessionRequest,
    current_user: UserResponse = Depends(get_payment_user("payments:write")),
    db: AsyncSession = Depends(get_db),
):
    """Create a Magpie Checkout Session and record a transaction."""
    try:
        svc = MagpieService()

        # Determine amount: prefer explicit amount, else sum line_items
        amount = data.amount
        if amount is None and data.line_items:
            try:
                total_cents = 0
                for item in data.line_items:
                    qty = int(float(item.get("quantity") or 1))
                    # amount in line_items is usually in cents for Magpie
                    item_amount = int(float(item.get("amount") or 0))
                    total_cents += item_amount * qty

                # Convert cents to main currency units (PHP) for our internal ledger
                amount = float(total_cents) / 100.0
            except Exception as e:
                logger.warning("Failed to calculate amount from line_items: %s", e)
                raise HTTPException(status_code=400, detail="Invalid line_items format")

        if amount is None or amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be provided and > 0")

        # Combine payment methods from both possible fields
        payment_methods = list(set((data.payment_methods or []) + (data.payment_method_types or [])))

        payload: Dict[str, Any] = {
            "amount": amount,
            "currency": (data.currency or "php").lower(),
            "external_id": data.external_id or f"magpie-session-{uuid.uuid4().hex[:12]}",
        }

        # Magpie specific mapping: ensure both fields are present if provided
        if payment_methods:
            payload["payment_methods"] = payment_methods
            payload["payment_method_types"] = payment_methods

        if data.line_items:
            payload["line_items"] = data.line_items
        if data.mode:
            payload["mode"] = data.mode
        if data.success_url:
            payload["success_url"] = data.success_url
        if data.cancel_url:
            payload["cancel_url"] = data.cancel_url
        if data.customer_email:
            payload["customer_email"] = data.customer_email
        if data.description:
            payload["description"] = data.description
        if data.metadata:
            payload["metadata"] = data.metadata

        # Create session via service
        try:
            res = await svc.create_session(payload=payload)
        except Exception as exc:
            logger.warning("Magpie checkout session request failed: %s", exc)
            res = {"success": False, "error": str(exc)}

        if not res or not res.get("success"):
            logger.warning("Magpie checkout session failed, falling back to create_checkout: %s", (res or {}).get("error"))
            # Fall back to the legacy checkout endpoint if sessions API is unavailable
            fallback = await svc.create_checkout(
                amount=amount,
                description=data.description or "Checkout session",
                external_id=payload.get("external_id", f"magpie-session-{uuid.uuid4().hex[:12]}"),
                customer_name="",
                customer_email=data.customer_email or "",
                payment_methods=payment_methods or None,
                metadata={
                    **(data.metadata or {}),
                    "descriptor": data.description or "",
                    "merchant_name": "",
                    "source": "magpie_legacy_checkout_session_fallback",
                },
            )
            if not fallback.get("success"):
                raise HTTPException(status_code=400, detail=fallback.get("error", "Failed to create session"))

            # Normalize fallback response to look like a session
            res = {
                "success": True,
                "session_id": fallback.get("checkout_id", ""),
                "checkout_id": fallback.get("checkout_id", ""),
                "checkout_url": fallback.get("checkout_url", ""),
                "payment_url": fallback.get("checkout_url", ""),
                "external_id": fallback.get("external_id", payload.get("external_id", "")),
                "raw": fallback,
            }

        # Record transaction in local database
        txn_svc = TransactionsService(db)
        txn_id = None
        try:
            txn = await txn_svc.create_transaction(
                user_id=str(current_user.id),
                transaction_type="checkout_session",
                amount=amount,
                external_id=res.get("external_id", payload.get("external_id")),
                gateway_id=res.get("session_id", ""),
                description=data.description or "Magpie checkout session",
                customer_name="",
                customer_email=data.customer_email or "",
                payment_url=res.get("payment_url", ""),
            )
            txn_id = txn.id
        except Exception as exc:
            logger.error("Failed to record transaction for Magpie session: %s", exc, exc_info=True)
            # Non-fatal: return success but note transaction not recorded
            return {
                "success": True,
                "data": res.get("raw", {}),
                "warning": "session created but transaction record failed",
                "payment_url": res.get("payment_url", ""),
                "session_id": res.get("session_id", "")
            }

        return {
            "success": True,
            "data": {
                "transaction_id": txn_id,
                "session_id": res.get("session_id", ""),
                "payment_url": res.get("payment_url", ""),
                "external_id": res.get("external_id", ""),
                "raw": res.get("raw", {})
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in create_checkout_session: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



@router.get("/health")
async def magpie_health():
    """Simple Magpie health and diagnostics endpoint.

    Calls Magpie `account/balance` to verify API credentials and connectivity.
    """
    svc = MagpieService()
    diagnostics = {
        "configured_api_key": bool(svc.api_key),
        "base_url": svc.base_url,
    }
    # Attempt to fetch balance (non-fatal)
    try:
        res = await svc.get_balance()
        diagnostics["magpie_ok"] = bool(res.get("success"))
        diagnostics["magpie_response"] = res.get("available") if res.get("success") else res.get("error")
    except Exception as e:
        diagnostics["magpie_ok"] = False
        diagnostics["magpie_response"] = str(e)
    return {"success": True, "diagnostics": diagnostics}
