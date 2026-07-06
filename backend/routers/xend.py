import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_payment_user
from schemas.auth import UserResponse
from services.magpie_service import MagpieService
from services.transactions import TransactionsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/xend", tags=["xend"])


class CreatePaymentRequest(BaseModel):
    amount: float
    description: str = ""
    descriptor: str = ""
    merchant_name: str = ""
    customer_name: str = ""
    customer_email: str = ""
    external_id: str = ""
    payment_methods: List[str] = Field(default_factory=list)


class PayQRPhRequest(BaseModel):
    qr_data: str
    amount: float
    description: str = ""
    merchant_name: str = ""
    reference_number: str = ""


PAYMENT_METHOD_ALIASES = {
    "visa": "visa",
    "mastercard": "mastercard",
    "jcb": "jcb",
    "amex": "amex",
    "american_express": "amex",
    "unionpay": "unionpay",
    "applepay": "apple_pay",
    "apple_pay": "apple_pay",
    "googlepay": "google_pay",
    "google_pay": "google_pay",
    "paypal": "paypal",
    "gcash": "gcash",
    "grabpay": "grabpay",
    "maya": "maya",
    "paymaya": "maya",
    "alipay": "alipay",
    "wechat": "wechat_pay",
    "wechatpay": "wechat_pay",
    "wechat_pay": "wechat_pay",
    "bank_transfer": "bank_transfer",
    "instapay": "instapay",
    "pesonet": "pesonet",
    "qr": "qrph",
    "qrph": "qrph",
}

SUPPORTED_PAYMENT_METHODS = sorted(set(PAYMENT_METHOD_ALIASES.values()))


def _normalize_payment_methods(methods: List[str]) -> tuple[List[str], List[str]]:
    normalized: List[str] = []
    invalid: List[str] = []
    for raw in methods or []:
        key = (raw or "").strip().lower().replace("-", "_").replace(" ", "_")
        if not key:
            continue
        mapped = PAYMENT_METHOD_ALIASES.get(key)
        if not mapped:
            invalid.append(raw)
            continue
        if mapped not in normalized:
            normalized.append(mapped)
    return normalized, invalid


@router.get("/payment-methods")
async def get_supported_payment_methods():
    return {
        "success": True,
        "source": "magpie",
        "payment_methods": SUPPORTED_PAYMENT_METHODS,
    }


@router.get("/ping")
async def ping_magpie(
    current_user: UserResponse = Depends(get_payment_user("payments:read")),
):
    """Check Magpie connectivity and API key validity."""
    service = MagpieService()
    if not service.api_key:
        return {
            "success": False,
            "configured": False,
            "base_url": service.base_url,
            "error": "MAGPIE_API_KEY is not set",
        }

    result = await service.get_balance()
    return {
        "success": result.get("success", False),
        "configured": True,
        "base_url": service.base_url,
        "error": result.get("error") if not result.get("success") else None,
    }


@router.get("/transaction-stats")
async def get_transaction_stats(
    current_user: UserResponse = Depends(get_payment_user("payments:read")),
    db: AsyncSession = Depends(get_db),
):
    txn_service = TransactionsService(db)
    stats = await txn_service.get_user_stats(str(current_user.id))
    return {"success": True, **stats}


async def _process_xend_request(
    db: AsyncSession,
    current_user: UserResponse,
    request: CreatePaymentRequest,
    transaction_type: str,
    external_prefix: str,
    use_qr: bool,
):
    payment_methods, invalid_methods = _normalize_payment_methods(request.payment_methods)
    if invalid_methods:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported payment method(s): {', '.join(invalid_methods)}. Supported: {', '.join(SUPPORTED_PAYMENT_METHODS)}",
        )

    service = MagpieService()
    try:
        result = await service.create_unified_checkout(
            amount=request.amount,
            description=request.description,
            transaction_type=transaction_type,
            external_prefix=external_prefix,
            use_qr=use_qr,
            merchant_name=request.merchant_name,
            descriptor=request.descriptor,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            payment_methods=payment_methods,
            external_id=request.external_id or None,
        )
    except Exception as exc:
        logger.exception("Magpie payment creation failed")
        return {"success": False, "message": "Payment creation failed", "error": str(exc)}

    if not result.get("success"):
        return {"success": False, "message": result.get("error", "Failed to create payment")}

    # Record transaction
    txn_id = None
    try:
        txn_service = TransactionsService(db)
        txn = await txn_service.create_transaction(
            user_id=str(current_user.id),
            transaction_type=transaction_type,
            amount=request.amount,
            external_id=result.get("external_id"),
            gateway_id=result.get("gateway_id"),
            description=request.description,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            payment_url=result.get("payment_url"),
        )
        txn_id = txn.id
    except Exception as exc:
        logger.error("Failed to record transaction: %s", exc, exc_info=True)

    return {
        "success": True,
        "message": f"magpie {transaction_type.replace('_', ' ')} created",
        "data": {
            "transaction_id": txn_id,
            **result
        },
    }


@router.post("/create-invoice")
async def create_invoice(
    data: CreatePaymentRequest,
    current_user: UserResponse = Depends(get_payment_user("payments:write")),
    db: AsyncSession = Depends(get_db),
):
    return await _process_xend_request(
        db=db,
        current_user=current_user,
        request=data,
        transaction_type="invoice",
        external_prefix="xend-inv",
        use_qr=False,
    )


@router.post("/create-payment-link")
async def create_payment_link(
    data: CreatePaymentRequest,
    current_user: UserResponse = Depends(get_payment_user("payments:write")),
    db: AsyncSession = Depends(get_db),
):
    return await _process_xend_request(
        db=db,
        current_user=current_user,
        request=data,
        transaction_type="payment_link",
        external_prefix="xend-pl",
        use_qr=False,
    )


@router.post("/create-qr-code")
async def create_qr_code(
    data: CreatePaymentRequest,
    current_user: UserResponse = Depends(get_payment_user("payments:write")),
    db: AsyncSession = Depends(get_db),
):
    return await _process_xend_request(
        db=db,
        current_user=current_user,
        request=data,
        transaction_type="qr_code",
        external_prefix="xend-qr",
        use_qr=True,
    )


@router.post("/pay-qrph")
async def pay_qrph(
    data: PayQRPhRequest,
    current_user: UserResponse = Depends(get_payment_user("payments:write")),
    db: AsyncSession = Depends(get_db),
):
    request = CreatePaymentRequest(
        amount=data.amount,
        description=data.description or data.merchant_name or "QRPH payment",
        merchant_name=data.merchant_name,
        external_id=data.reference_number,
        payment_methods=["qrph"],
    )
    return await _process_xend_request(
        db=db,
        current_user=current_user,
        request=request,
        transaction_type="qrph_payment",
        external_prefix="xend-qrph",
        use_qr=True,
    )
