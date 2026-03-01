import httpx
import pytest

from server.client212 import Client212
from server.errors import Trading212APIError


def test_raise_on_error_has_structured_json_payload():
    client = Client212("id", "secret", "https://example.com")
    response = httpx.Response(401, json={"error": "unauthorized"})

    with pytest.raises(Trading212APIError) as exc:
        client.raise_on_error(response, "https://example.com/equity/account/info", "GET")

    error = exc.value
    assert error.status_code == 401
    assert error.method == "GET"
    assert error.payload == {"error": "unauthorized"}


def test_raise_on_error_uses_text_payload_when_json_missing():
    client = Client212("id", "secret", "https://example.com")
    response = httpx.Response(500, text="internal failure")

    with pytest.raises(Trading212APIError) as exc:
        client.raise_on_error(response, "https://example.com/equity/orders", "POST")

    assert exc.value.payload == "internal failure"


def test_make_headers_uses_basic_auth_prefix():
    client = Client212("id", "secret", "https://example.com")

    headers = client.make_headers()

    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Basic ")


@pytest.mark.asyncio
async def test_place_limit_order_builds_expected_payload(monkeypatch):
    client = Client212("id", "secret", "https://example.com")
    captured = {}

    async def fake_post(path, data):
        captured["path"] = path
        captured["data"] = data
        return {"ok": True}

    monkeypatch.setattr(client, "post", fake_post)

    await client.place_limit_order(
        limit_price=123.45,
        quantity=1.25,
        ticker="AAPL_US_EQ",
        time_validity=Client212.TimeValidity.DAY,
    )

    assert captured["path"] == "equity/orders/limit"
    assert captured["data"] == {
        "limitPrice": 123.45,
        "quantity": 1.25,
        "ticker": "AAPL_US_EQ",
        "timeValidity": "DAY",
    }
