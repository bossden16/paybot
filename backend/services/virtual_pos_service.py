"""Virtual POS Service - Payment processing & wallet management."""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from models.virtual_pos import (
    VirtualWallet,
    LedgerEntry,
    LedgerEntryType,
    LedgerEntryStatus,
    CardSettlementBatch,
)

logger = logging.getLogger(__name__)


class VirtualPOSService:
    """Service layer for Virtual POS Terminal operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_wallet(self, wallet_id: str, user_id: Optional[str] = None) -> VirtualWallet:
        """Get existing wallet or create new one."""
        stmt = select(VirtualWallet).where(VirtualWallet.wallet_id == wallet_id)
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            wallet = VirtualWallet(
                wallet_id=wallet_id,
                user_id=user_id,
                available_balance=0,
                pending_balance=0,
                currency="PHP"
            )
            self.db.add(wallet)
            await self.db.flush()
        
        return wallet

    async def process_qr_charge(
        self,
        wallet_id: str,
        amount_pesos: float,
        payment_method: str = "QRPH",
    ) -> Dict[str, Any]:
        """Process QR payment (instant credit)."""
        amount_centavos = int(round(amount_pesos * 100))
        
        if amount_centavos <= 0:
            raise ValueError("Amount must be greater than zero")
        
        wallet = await self.get_or_create_wallet(wallet_id)
        
        entry = LedgerEntry(
            wallet_id=wallet_id,
            entry_type=LedgerEntryType.QR_DEPOSIT_INSTANT,
            amount_centavos=amount_centavos,
            external_reference=f"REF-{uuid.uuid4().hex[:8].upper()}",
            payment_method=payment_method,
            description=f"{payment_method} instant deposit",
            status=LedgerEntryStatus.SUCCESS,
            settled_at=datetime.utcnow(),
        )
        self.db.add(entry)
        
        wallet.available_balance += amount_centavos
        wallet.total_lifetime += amount_centavos
        await self.db.flush()
        
        logger.info(f"QR charge processed: {wallet_id} +₱{amount_pesos}")
        
        return {
            "success": True,
            "reference_no": entry.external_reference,
            "settlement": "INSTANT_CREDIT",
            "wallet": self._serialize_wallet(wallet),
        }

    async def process_card_charge(
        self,
        wallet_id: str,
        amount_pesos: float,
        card_type: str = "VISA",
    ) -> Dict[str, Any]:
        """Process card payment (pending T+1)."""
        amount_centavos = int(round(amount_pesos * 100))
        
        if amount_centavos <= 0:
            raise ValueError("Amount must be greater than zero")
        
        wallet = await self.get_or_create_wallet(wallet_id)
        
        entry = LedgerEntry(
            wallet_id=wallet_id,
            entry_type=LedgerEntryType.CARD_DEPOSIT_PENDING,
            amount_centavos=amount_centavos,
            external_reference=f"MAYA-{uuid.uuid4().hex[:8].upper()}",
            payment_method=card_type,
            description=f"{card_type} card payment (pending T+1)",
            status=LedgerEntryStatus.SUCCESS,
            settled_at=datetime.utcnow(),
        )
        self.db.add(entry)
        
        wallet.pending_balance += amount_centavos
        wallet.total_lifetime += amount_centavos
        await self.db.flush()
        
        logger.info(f"Card charge processed: {wallet_id} +₱{amount_pesos} (pending)")
        
        return {
            "success": True,
            "reference_no": entry.external_reference,
            "settlement": "PENDING_T1",
            "wallet": self._serialize_wallet(wallet),
        }

    async def process_withdrawal(
        self,
        wallet_id: str,
        amount_pesos: float,
        bank_code: str,
        account_number: str,
    ) -> Dict[str, Any]:
        """Process InstaPay withdrawal with atomic balance check."""
        amount_centavos = int(round(amount_pesos * 100))
        
        if amount_centavos <= 0:
            raise ValueError("Amount must be greater than zero")
        
        if amount_centavos > 5000000:
            raise ValueError("InstaPay transaction limit: ₱50,000.00 per transaction")
        
        wallet = await self.get_or_create_wallet(wallet_id)
        
        if wallet.available_balance < amount_centavos:
            raise ValueError(
                f"Insufficient available balance. Available: ₱{wallet.available_balance / 100:.2f}, "
                f"Requested: ₱{amount_pesos}"
            )
        
        wallet.available_balance -= amount_centavos
        await self.db.flush()
        
        entry = LedgerEntry(
            wallet_id=wallet_id,
            entry_type=LedgerEntryType.WITHDRAWAL_OUT,
            amount_centavos=amount_centavos,
            external_reference=f"WD-INSTAPAY-{uuid.uuid4().hex[:8].upper()}",
            payment_method="INSTAPAY",
            description=f"InstaPay to {bank_code} {account_number}",
            status=LedgerEntryStatus.SUCCESS,
            settled_at=datetime.utcnow(),
        )
        self.db.add(entry)
        await self.db.flush()
        
        logger.info(f"Withdrawal processed: {wallet_id} -₱{amount_pesos} via InstaPay")
        
        return {
            "success": True,
            "reference_no": entry.external_reference,
            "message": "Disbursement finalized through InstaPay.",
            "wallet": self._serialize_wallet(wallet),
        }

    async def process_daily_card_sweep(self) -> Dict[str, Any]:
        """Process T+1 daily card settlement batch."""
        stmt = select(VirtualWallet).where(VirtualWallet.pending_balance > 0)
        result = await self.db.execute(stmt)
        wallets = result.scalars().all()
        
        total_cleared = 0
        swept_count = 0
        
        for wallet in wallets:
            pending_amount = wallet.pending_balance
            wallet.available_balance += pending_amount
            wallet.pending_balance = 0
            
            entry = LedgerEntry(
                wallet_id=wallet.wallet_id,
                entry_type=LedgerEntryType.CARD_BALANCE_CLEARED,
                amount_centavos=pending_amount,
                external_reference=f"SWEEP-{uuid.uuid4().hex[:8].upper()}",
                payment_method="DAILY_SWEEP",
                description="Daily T+1 card settlement batch processing",
                status=LedgerEntryStatus.SUCCESS,
                settled_at=datetime.utcnow(),
            )
            self.db.add(entry)
            
            total_cleared += pending_amount
            swept_count += 1
        
        batch = CardSettlementBatch(
            batch_date=datetime.utcnow().strftime("%Y-%m-%d"),
            total_cleared=total_cleared,
            wallet_count=swept_count,
            status="COMPLETED",
        )
        self.db.add(batch)
        await self.db.flush()
        
        logger.info(f"Daily card sweep completed: {swept_count} wallets, ₱{total_cleared/100:.2f} cleared")
        
        return {
            "success": True,
            "message": f"Completed morning clearing. Accounts updated: {swept_count}",
            "total_cleared": total_cleared,
            "wallet_count": swept_count,
        }

    async def get_wallet_with_history(self, wallet_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get wallet state with recent transaction history."""
        wallet = await self.get_or_create_wallet(wallet_id)
        
        stmt = (
            select(LedgerEntry)
            .where(LedgerEntry.wallet_id == wallet_id)
            .order_by(desc(LedgerEntry.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        entries = result.scalars().all()
        
        return {
            "wallet": self._serialize_wallet(wallet),
            "history": [self._serialize_ledger_entry(e) for e in entries],
        }

    @staticmethod
    def _serialize_wallet(wallet: VirtualWallet) -> Dict[str, Any]:
        """Serialize wallet to JSON-compatible dict."""
        return {
            "wallet_id": wallet.wallet_id,
            "available_balance": wallet.available_balance,
            "pending_balance": wallet.pending_balance,
            "total_lifetime": wallet.total_lifetime,
            "currency": wallet.currency,
        }

    @staticmethod
    def _serialize_ledger_entry(entry: LedgerEntry) -> Dict[str, Any]:
        """Serialize ledger entry to JSON-compatible dict."""
        return {
            "id": entry.id,
            "wallet_id": entry.wallet_id,
            "type": entry.entry_type.value,
            "status": entry.status.value,
            "amount_centavos": entry.amount_centavos,
            "external_reference": entry.external_reference,
            "payment_method": entry.payment_method,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }
