import asyncio
import pytest

from services.magpie_service import MagpieService


class DummyResp:
    def __init__(self, status_code, text, data):
        self.status_code = status_code
        self._text = text
        self._data = data

    @property
    def text(self):
        return self._text

    def json(self):
        return self._data


class DummyClient:
    def __init__(self, *args, **kwargs):
        # shared state across context
        self.attempt = getattr(DummyClient, "attempt", 0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None):
        DummyClient.attempt = getattr(DummyClient, "attempt", 0) + 1
        if DummyClient.attempt == 1:
            return DummyResp(500, '{"message":"Internal server error"}', {"message": "Internal server error"})
        return DummyResp(200, '{"id":"ok"}', {"id": "ok"})


@pytest.mark.asyncio
async def test_post_retries(monkeypatch):
    # Monkeypatch httpx.AsyncClient used in service
    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    svc = MagpieService()
    svc.api_key = "testkey"
    result = await svc._post("/v1/test", {"foo": "bar"})
    assert result.get("success") is True
    assert result.get("data", {}).get("id") == "ok"
