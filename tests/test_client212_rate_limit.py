import asyncio
import time

import httpx
import pytest

from server.client212 import RateLimit


@pytest.mark.asyncio
async def test_wait_if_needed_sleeps_non_blocking(monkeypatch):
    calls: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    rate_limit = RateLimit(remaining=0, reset=int(time.time()) + 2)
    await rate_limit.wait_if_needed()

    assert len(calls) == 1
    assert calls[0] >= 2


@pytest.mark.asyncio
async def test_wait_if_needed_no_sleep_if_remaining_available(monkeypatch):
    calls: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    rate_limit = RateLimit(remaining=1, reset=int(time.time()) + 10)
    await rate_limit.wait_if_needed()

    assert calls == []


def test_from_headers_parses_defaults_and_values():
    headers = httpx.Headers(
        {
            "x-ratelimit-limit": "120",
            "x-ratelimit-period": "60",
            "x-ratelimit-remaining": "119",
            "x-ratelimit-reset": "1700000000",
            "x-ratelimit-used": "1",
        }
    )

    parsed = RateLimit.from_headers(headers)

    assert parsed.limit == 120
    assert parsed.period == 60
    assert parsed.remaining == 119
    assert parsed.reset == 1700000000
    assert parsed.used == 1
