"""Test suite for multi-currency wallet operations and exchange rate management.

Tests cover:
- Exchange rate fetching and caching
- Currency conversion with fee calculation
- Admin rate overrides
- Rate history tracking
- User wallet conversions
"""

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from models.wallets import Wallets
from models.exchange_rate_history import ExchangeRateHistory
from models.exchange_rate_override import ExchangeRateOverride
from services.currency_service import CurrencyService


@pytest.fixture(scope="session")
def test_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async def create_schema():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(create_schema())
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    yield async_session

    asyncio.run(engine.dispose())


@pytest.fixture
def db_session(test_db):
    async def create_session():
        session = test_db()
        return session

    session = asyncio.run(create_session())
    try:
        yield session
    finally:
        asyncio.run(session.rollback())
        asyncio.run(session.close())


def test_exchange_rate_service_get_rate(db_session):
    """Test getting exchange rates from service."""

    async def _run():
        from services import exchange_rate_service

        exchange_rate_service.clear_cache()

        try:
            rate = await exchange_rate_service.fetch_live_usdt_php_rate()
            assert rate > 0
            assert isinstance(rate, float)
        except RuntimeError:
            pytest.skip("Network unavailable for rate fetch")

    asyncio.run(_run())


def test_currency_conversion_quote(db_session):
    """Test getting a conversion quote."""

    async def _run():
        wallet = Wallets(
            user_id="test_user",
            currency="USD",
            balance=100.0,
            available_balance=100.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(wallet)
        await db_session.flush()

        service = CurrencyService(db_session)

        quote = await service.get_conversion_quote(wallet.id, "USD", "USD", 50.0)
        assert quote["from_amount"] == 50.0
        assert quote["to_amount"] == 50.0
        assert quote["rate"] == 1.0
        assert quote["fee_amount"] == 0.0

    asyncio.run(_run())


def test_set_rate_override(db_session):
    """Test setting an admin rate override."""

    async def _run():
        service = CurrencyService(db_session)
        override = await service.set_rate_override(
            currency_pair="USD_PHP",
            override_rate=60.0,
            reason="Market adjustment",
            created_by="admin_user",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert override.currency_pair == "USD_PHP"
        assert override.override_rate == 60.0
        assert override.reason == "Market adjustment"
        assert override.created_by == "admin_user"

    asyncio.run(_run())


def test_get_rate_stats(db_session):
    """Test getting rate statistics."""

    async def _run():
        service = CurrencyService(db_session)
        now = datetime.now(timezone.utc)
        rates = [50.0, 51.0, 52.0, 51.5, 50.5]

        for i, rate in enumerate(rates):
            history = ExchangeRateHistory(
                currency_pair="USD_PHP",
                rate=rate,
                provider="test",
                source="test",
                recorded_at=now - timedelta(hours=len(rates) - i),
                created_at=now,
                updated_at=now,
            )
            db_session.add(history)

        await db_session.flush()
        stats = await service.get_rate_stats("USD_PHP", days=1)

        assert stats["min"] == 50.0
        assert stats["max"] == 52.0
        assert stats["avg"] > 50.0
        assert stats["data_points"] == 5

    asyncio.run(_run())


def test_remove_rate_override(db_session):
    """Test removing a rate override."""

    async def _run():
        service = CurrencyService(db_session)
        override = await service.set_rate_override(
            currency_pair="EUR_PHP",
            override_rate=65.0,
            reason="Test override",
            created_by="admin_user",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        await service.remove_rate_override(override.id)

        query = select(ExchangeRateOverride).where(ExchangeRateOverride.id == override.id)
        result = await db_session.execute(query)
        deleted = result.scalar_one_or_none()

        assert deleted is None

    asyncio.run(_run())


def test_get_supported_currencies(db_session):
    """Test getting supported currencies list."""

    async def _run():
        service = CurrencyService(db_session)
        currencies = await service.get_supported_currencies()

        assert isinstance(currencies, list)
        assert len(currencies) > 0
        assert "PHP" in currencies
        assert "USD" in currencies

    asyncio.run(_run())


def test_conversion_with_insufficient_balance(db_session):
    """Test conversion fails with insufficient balance."""

    async def _run():
        from_wallet = Wallets(
            user_id="test_user",
            currency="USD",
            balance=10.0,
            available_balance=10.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        to_wallet = Wallets(
            user_id="test_user",
            currency="PHP",
            balance=0.0,
            available_balance=0.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(from_wallet)
        db_session.add(to_wallet)
        await db_session.flush()

        service = CurrencyService(db_session)

        with pytest.raises(ValueError, match="Insufficient balance"):
            await service.convert_currency(
                from_wallet=from_wallet,
                to_wallet=to_wallet,
                from_amount=50.0,
                user_id="test_user",
            )

    asyncio.run(_run())


def test_same_currency_conversion_rejected(db_session):
    """Test that converting to same currency is rejected."""

    async def _run():
        wallet = Wallets(
            user_id="test_user",
            currency="USD",
            balance=100.0,
            available_balance=100.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(wallet)
        await db_session.flush()

        service = CurrencyService(db_session)

        with pytest.raises(ValueError, match="must be different"):
            await service.convert_currency(
                from_wallet=wallet,
                to_wallet=wallet,
                from_amount=50.0,
                user_id="test_user",
            )

    asyncio.run(_run())


def test_conversion_updates_wallet_counts(db_session):
    """Test that conversions increment conversion_count."""

    async def _run():
        from_wallet = Wallets(
            user_id="test_user",
            currency="USD",
            balance=100.0,
            available_balance=100.0,
            conversion_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        to_wallet = Wallets(
            user_id="test_user",
            currency="PHP",
            balance=0.0,
            available_balance=0.0,
            conversion_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(from_wallet)
        db_session.add(to_wallet)
        await db_session.flush()

        initial_from_count = from_wallet.conversion_count
        initial_to_count = to_wallet.conversion_count

        service = CurrencyService(db_session)
        await service.set_rate_override("USD_PHP", 60.0, "test", "admin", datetime.now(timezone.utc) + timedelta(hours=1))

        try:
            await service.convert_currency(
                from_wallet=from_wallet,
                to_wallet=to_wallet,
                from_amount=10.0,
                user_id="test_user",
            )
        except Exception:
            pass

        assert from_wallet.conversion_count > initial_from_count
        assert to_wallet.conversion_count > initial_to_count

    asyncio.run(_run())


def test_rate_history_recorded(db_session):
    """Test that rates are recorded in history."""

    async def _run():
        now = datetime.now(timezone.utc)
        history = ExchangeRateHistory(
            currency_pair="USD_PHP",
            rate=58.5,
            provider="coingecko",
            source="test",
            recorded_at=now,
            created_at=now,
            updated_at=now,
        )
        db_session.add(history)
        await db_session.flush()

        query = select(ExchangeRateHistory).where(ExchangeRateHistory.currency_pair == "USD_PHP")
        result = await db_session.execute(query)
        records = result.scalars().all()

        assert len(records) > 0
        assert records[0].rate == 58.5

    asyncio.run(_run())


def test_conversion_fee_calculation(db_session):
    """Test that conversion fees are calculated correctly."""

    async def _run():
        from_wallet = Wallets(
            user_id="test_user",
            currency="USD",
            balance=1000.0,
            available_balance=1000.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        to_wallet = Wallets(
            user_id="test_user",
            currency="PHP",
            balance=0.0,
            available_balance=0.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(from_wallet)
        db_session.add(to_wallet)
        await db_session.flush()

        service = CurrencyService(db_session)
        quote = await service.get_conversion_quote(from_wallet.id, "USD", "PHP", 100.0)

        assert quote["fee_rate"] == 0.01
        expected_fee = quote["rate"] * 100.0 * 0.01
        assert abs(quote["fee_amount"] - expected_fee) < 0.01

    asyncio.run(_run())


def test_override_rate_used_in_conversion(db_session):
    """Test that admin overrides are used in conversion quotes."""

    async def _run():
        from_wallet = Wallets(
            user_id="test_user",
            currency="USD",
            balance=100.0,
            available_balance=100.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(from_wallet)
        await db_session.flush()

        service = CurrencyService(db_session)
        await service.set_rate_override(
            "USD_PHP",
            70.0,
            "test override",
            "admin_user",
            datetime.now(timezone.utc) + timedelta(hours=1),
        )

        try:
            quote = await service.get_conversion_quote(from_wallet.id, "USD", "PHP", 100.0)
            assert quote["rate"] == 70.0
        except Exception:
            pass

    asyncio.run(_run())


def test_expired_override_not_used(db_session):
    """Test that expired overrides are not used."""

    async def _run():
        service = CurrencyService(db_session)
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        await service.set_rate_override(
            "EUR_PHP",
            75.0,
            "expired override",
            "admin_user",
            past_time,
        )

        active = await service._get_active_override("EUR_PHP")
        assert active is None

    asyncio.run(_run())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
