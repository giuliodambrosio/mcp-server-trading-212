import httpx
import pytest

from server.client212 import Client212


@pytest.mark.asyncio
async def test_adjust_to_rate_limits_retries_until_success():
    client = Client212("id", "secret", "https://example.com")
    attempts = 0

    async def request() -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(429, headers={"x-ratelimit-remaining": "1"})
        return httpx.Response(200, json={"ok": True}, headers={"x-ratelimit-remaining": "1"})

    response = await client.adjust_to_rate_limits(request)

    assert attempts == 3
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_adjust_to_rate_limits_stops_after_max_retries():
    client = Client212("id", "secret", "https://example.com")
    attempts = 0

    async def request() -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429, headers={"x-ratelimit-remaining": "1"})

    response = await client.adjust_to_rate_limits(request)

    assert attempts == 4  # initial try + 3 retries
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_adjust_to_rate_limits_no_retry_on_non_429():
    client = Client212("id", "secret", "https://example.com")
    attempts = 0

    async def request() -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(500)

    response = await client.adjust_to_rate_limits(request)

    assert attempts == 1
    assert response.status_code == 500
