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
from routers import xend

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/magpie", tags=["magpie-legacy"])


class CheckoutSessionRequest(BaseModel):
    payment_method_types: List[str] = Field(default_factory=list)
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
    svc = MagpieService()

    # Determine amount: prefer explicit amount, else sum line_items
    amount = data.amount
    if amount is None and data.line_items:
        try:
            total = 0.0
            for item in data.line_items:
                qty = float(item.get("quantity", 1))
                item_amount = float(item.get("amount", 0))
                total += item_amount * qty
            # If totals look like cents, convert to main currency units
            if total > 1000:
                total = total / 100.0
            amount = float(total)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid line_items format")

    if not amount or amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be provided and > 0")

    payload: Dict[str, Any] = {
        "amount": amount,
        "currency": data.currency,
        "external_id": data.external_id or f"magpie-session-{uuid.uuid4().hex[:12]}",
    }
    if data.payment_method_types:
        payload["payment_method_types"] = data.payment_method_types
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

    if not res.get("success"):
        logger.warning("Magpie checkout session failed, falling back to create_checkout: %s", res.get("error"))
        # Magpie's checkout-session endpoint can return a generic 500 even when the
        # underlying checkout flow is available. Fall back to the checkout endpoint.
        fallback = await svc.create_checkout(
            amount=amount,
            description=data.description or "Checkout session",
            external_id=payload.get("external_id", f"magpie-session-{uuid.uuid4().hex[:12]}"),
            customer_name="",
            customer_email=data.customer_email or "",
            metadata={
                **(data.metadata or {}),
                "descriptor": data.description or "",
                "merchant_name": "",
                "source": "magpie_legacy_checkout_session_fallback",
            },
        )
        if not fallback.get("success"):
            raise HTTPException(status_code=400, detail=fallback.get("error", "Failed to create session"))
        res = {
            "success": True,
            "session_id": fallback.get("checkout_id", ""),
            "payment_url": fallback.get("checkout_url", ""),
            "external_id": fallback.get("external_id", payload.get("external_id", "")),
            "raw": fallback,
        }

    # Record transaction
    txn_svc = TransactionsService(db)
    try:
        txn = await txn_svc.create_transaction(
            user_id=str(current_user.id),
            transaction_type="checkout_session",
            amount=amount,
            external_id=res.get("external_id", payload.get("external_id")),
            gateway_id=res.get("session_id", ""),
            description=data.description,
            customer_name="",
            customer_email=data.customer_email or "",
            payment_url=res.get("payment_url", ""),
        )
    except Exception:
        # Non-fatal: return success but note transaction not recorded
        return {"success": True, "data": res.get("raw", {}), "warning": "session created but transaction record failed"}

    return {"success": True, "data": {"transaction_id": txn.id, **res}}


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
