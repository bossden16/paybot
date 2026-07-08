from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Index, Integer, String

from core.database import Base


class ExchangeRateHistory(Base):
    """Track exchange rate history for analytics and reporting."""
    __tablename__ = "exchange_rate_history"
    __table_args__ = (
        # Index for querying rates by currency pair
        Index("idx_xrate_history_pair", "currency_pair"),
        # Index for querying rates by date (for analytics)
        Index("idx_xrate_history_recorded", "recorded_at"),
        # Composite index for efficient range queries
        Index("idx_xrate_history_pair_date", "currency_pair", "recorded_at"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    currency_pair = Column(String, nullable=False)  # e.g., "USDT_PHP", "USD_EUR"
    from_currency = Column(String, nullable=False, default="", server_default="")
    to_currency = Column(String, nullable=False, default="", server_default="")
    rate = Column(Float, nullable=False)  # Exchange rate (e.g., 56.75 for USDT→PHP)
    provider = Column(String, nullable=False)  # Source: "coingecko", "yahoo_finance", "manual"
    source = Column(String, nullable=True)  # Additional context (e.g., API endpoint, override reason)
    
    # Metadata
    recorded_at = Column(DateTime(timezone=True), nullable=False)  # When this rate was recorded
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
