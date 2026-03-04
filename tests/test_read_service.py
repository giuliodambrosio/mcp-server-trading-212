from __future__ import annotations

import pytest

from server.errors import ResourceNotFoundError
from server.read_service import ReadService


class FakeClient:
    async def get_account_info(self):
        return {"kind": "info"}

    async def get_balance(self):
        return {"kind": "balance"}

    async def get_portfolio(self):
        return [{"ticker": "AAPL_US_EQ"}]

    async def get_portfolio_entry(self, ticker: str):
        return {"ticker": ticker}

    async def get_orders(self):
        return [{"id": 1}]

    async def get_order(self, order_id: int):
        return {"id": order_id}

    async def get_pies(self):
        return [{"id": 10}]

    async def get_pie(self, pie_id: int):
        return {"id": pie_id}

    async def get_paid_dividends(self):
        return [{"ticker": "AAPL_US_EQ"}]

    async def get_exchanges(self):
        return [{"id": "NYSE"}]

    async def get_instruments(self):
        return [
            {"ticker": "AAPL_US_EQ", "currencyCode": "USD"},
            {"ticker": "MSFT_US_EQ", "currencyCode": "USD"},
        ]


def test_read_service_requires_at_least_one_client():
    with pytest.raises(ValueError, match="At least one account"):
        ReadService({}, "isa")


def test_read_service_requires_valid_default_account():
    with pytest.raises(ValueError, match="default_account"):
        ReadService({"isa": FakeClient()}, "invest")


def test_get_client_falls_back_to_default_and_lists_accounts():
    service = ReadService({"isa": FakeClient(), "invest": FakeClient()}, "isa")

    assert service.get_client() is service.clients["isa"]
    assert service.list_accounts() == ["isa", "invest"]


def test_get_client_raises_for_unknown_account():
    service = ReadService({"isa": FakeClient()}, "isa")

    with pytest.raises(ResourceNotFoundError, match="account"):
        service.get_client("unknown")


@pytest.mark.asyncio
async def test_read_service_methods_delegate_to_selected_client():
    service = ReadService({"isa": FakeClient(), "invest": FakeClient()}, "isa")

    assert await service.get_account_info("invest") == {"kind": "info"}
    assert await service.get_balance("invest") == {"kind": "balance"}
    assert await service.get_portfolio("invest") == [{"ticker": "AAPL_US_EQ"}]
    assert await service.get_portfolio_entry("AAPL_US_EQ", "invest") == {"ticker": "AAPL_US_EQ"}
    assert await service.get_orders("invest") == [{"id": 1}]
    assert await service.get_order(1, "invest") == {"id": 1}
    assert await service.get_pies("invest") == [{"id": 10}]
    assert await service.get_pie(10, "invest") == {"id": 10}
    assert await service.get_dividends("invest") == [{"ticker": "AAPL_US_EQ"}]
    assert await service.get_exchanges("invest") == [{"id": "NYSE"}]
    assert await service.get_instruments("invest") == [
        {"ticker": "AAPL_US_EQ", "currencyCode": "USD"},
        {"ticker": "MSFT_US_EQ", "currencyCode": "USD"},
    ]
    assert await service.get_instrument_tickers("invest") == ["AAPL_US_EQ", "MSFT_US_EQ"]
    assert await service.get_instrument_by_ticker("AAPL_US_EQ", "invest") == {
        "ticker": "AAPL_US_EQ",
        "currencyCode": "USD",
    }


@pytest.mark.asyncio
async def test_get_instrument_by_ticker_raises_when_missing():
    service = ReadService({"isa": FakeClient()}, "isa")

    with pytest.raises(ResourceNotFoundError, match="instrument"):
        await service.get_instrument_by_ticker("MISSING_EQ", "isa")
