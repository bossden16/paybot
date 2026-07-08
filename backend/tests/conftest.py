import os

import pytest
from _pytest.monkeypatch import MonkeyPatch

# Ensure background tasks are disabled during tests to avoid flakiness
os.environ.setdefault("DISABLE_BACKGROUND_TASKS", "1")

try:
    import pytest_asyncio  # noqa: F401
except ImportError:
    pytest_asyncio = None

pytest_plugins = ["pytest_asyncio"]


class _MonkeypatchCompat:
    def context(self):
        return MonkeyPatch.context()


if not hasattr(pytest, "monkeypatch"):
    pytest.monkeypatch = _MonkeypatchCompat()
