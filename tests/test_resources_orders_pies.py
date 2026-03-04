import json

import pytest

from server.errors import ResourceNotFoundError
from server.resources import (
    resource_dividends,
    resource_exchanges,
    resource_instrument_ticker,
    resource_instrument_tickers,
    resource_order_id,
    resource_orders,
    resource_pie_id,
    resource_pies,
)


class FakeReadService:
    async def get_orders(self, account: str):
        assert account == "isa"
        return [{"id": 1}]

    async def get_order(self, order_id: int, account: str):
        assert account == "isa"
        return {"id": order_id}

    async def get_pies(self, account: str):
        assert account == "isa"
        return [{"id": 10}]

    async def get_pie(self, pie_id: int, account: str):
        assert account == "isa"
        return {"id": pie_id}

    async def get_dividends(self, account: str):
        assert account == "isa"
        return [{"ticker": "AAPL_US_EQ"}]

    async def get_exchanges(self, account: str):
        assert account == "isa"
        return [{"id": "NYSE"}]

    async def get_instrument_tickers(self, account: str):
        assert account == "isa"
        return ["AAPL_US_EQ"]

    async def get_instrument_by_ticker(self, ticker: str, account: str):
        assert account == "isa"
        return {"ticker": ticker, "currencyCode": "USD"}


@pytest.mark.asyncio
async def test_orders_and_order_resources():
    service = FakeReadService()
    orders = json.loads(await resource_orders(service, "isa"))
    order = json.loads(await resource_order_id(service, "isa", 22))

    assert orders["data"] == [{"id": 1}]
    assert order["data"] == {"id": 22}


@pytest.mark.asyncio
async def test_pies_and_pie_resources():
    service = FakeReadService()
    pies = json.loads(await resource_pies(service, "isa"))
    pie = json.loads(await resource_pie_id(service, "isa", 44))

    assert pies["data"] == [{"id": 10}]
    assert pie["data"] == {"id": 44}


@pytest.mark.asyncio
async def test_metadata_and_dividends_resources():
    service = FakeReadService()
    dividends = json.loads(await resource_dividends(service, "isa"))
    exchanges = json.loads(await resource_exchanges(service, "isa"))
    tickers = json.loads(await resource_instrument_tickers(service, "isa"))
    instrument = json.loads(await resource_instrument_ticker(service, "isa", "AAPL_US_EQ"))

    assert dividends["data"] == [{"ticker": "AAPL_US_EQ"}]
    assert exchanges["data"] == [{"id": "NYSE"}]
    assert tickers["data"] == ["AAPL_US_EQ"]
    assert instrument["data"]["ticker"] == "AAPL_US_EQ"


@pytest.mark.asyncio
async def test_instrument_resource_propagates_not_found():
    class MissingInstrumentService(FakeReadService):
        async def get_instrument_by_ticker(self, ticker: str, account: str):
            raise ResourceNotFoundError("instrument", ticker)

    with pytest.raises(ResourceNotFoundError):
        await resource_instrument_ticker(MissingInstrumentService(), "isa", "MISSING_EQ")
