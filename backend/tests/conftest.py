import os
# Ensure background tasks are disabled during tests to avoid flakiness
os.environ.setdefault("DISABLE_BACKGROUND_TASKS", "1")

try:
    import pytest_asyncio  # noqa: F401
except ImportError:
    pytest_asyncio = None

pytest_plugins = ["pytest_asyncio"]
