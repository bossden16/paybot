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


@pytest.mark.asyncio
async def test_create_checkout_falls_back_to_session_when_checkout_endpoint_fails(monkeypatch):
    svc = MagpieService()
    svc.api_key = "testkey"

    async def fake_post(path, payload, idempotency_key=None, extra_headers=None):
        if path == "/v1/payments/checkout":
            return {"success": False, "error": "checkout failed"}
        if path == "/v1/checkout/sessions":
            return {
                "success": True,
                "data": {
                    "id": "session-123",
                    "payment_url": "https://magpie.example/session/123",
                    "external_id": payload.get("external_id"),
                },
            }
        return {"success": False, "error": "unexpected path"}

    monkeypatch.setattr(svc, "_post", fake_post)

    result = await svc.create_checkout(
        amount=100.0,
        description="wallet top up",
        external_id="ext-1",
    )

    assert result.get("success") is True
    assert result.get("checkout_id") == "session-123"
    assert result.get("checkout_url") == "https://magpie.example/session/123"
    assert result.get("external_id") == "ext-1"


@pytest.mark.asyncio
async def test_create_checkout_sends_payment_methods_top_level(monkeypatch):
    svc = MagpieService()
    svc.api_key = "testkey"
    captured = {}

    async def fake_post(path, payload, idempotency_key=None, extra_headers=None):
        captured["path"] = path
        captured["payload"] = payload
        return {
            "success": True,
            "data": {
                "checkout_id": "co_123",
                "checkout_url": "https://magpie.example/checkout/co_123",
                "external_id": payload.get("external_id"),
            },
        }

    monkeypatch.setattr(svc, "_post", fake_post)

    result = await svc.create_checkout(
        amount=100.0,
        description="test",
        external_id="ext-1",
        payment_methods=["gcash", "card"],
        metadata={"source": "magpie"},
    )

    assert result.get("success") is True
    assert captured["path"] == "/v1/payments/checkout"
    assert captured["payload"]["payment_methods"] == ["gcash", "card"]
    assert captured["payload"]["metadata"] == {"source": "magpie"}
    assert result.get("checkout_id") == "co_123"
