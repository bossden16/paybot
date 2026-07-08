import pytest

from core.config import Settings


def test_production_settings_reject_placeholder_secrets():
    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings(
            environment="production",
            jwt_secret_key="your_secure_random_secret_key_here",
            telegram_bot_token="123456:TEST_BOT_TOKEN",
            database_url="sqlite+aiosqlite:///./paybot.db",
        )


def test_development_settings_allow_missing_secrets():
    settings = Settings(
        environment="development",
        jwt_secret_key="",
        telegram_bot_token="",
        database_url="sqlite+aiosqlite:///./paybot.db",
    )

    assert settings.environment == "development"
    assert settings.jwt_secret_key
