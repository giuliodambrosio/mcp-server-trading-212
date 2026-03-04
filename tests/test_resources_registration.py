from __future__ import annotations

import json

import pytest

from server.resources import register_resources
from tests.helpers import FakeMCP


class FakeReadService:
    async def get_account_info(self, account: str):
        return {"account": account}

    async def get_balance(self, account: str):
        return {"account": account, "free": 100}

    async def get_portfolio(self, account: str):
        return [{"account": account, "ticker": "AAPL_US_EQ"}]

    async def get_portfolio_entry(self, ticker: str, account: str):
        return {"account": account, "ticker": ticker}

    async def get_orders(self, account: str):
        return [{"account": account, "id": 1}]

    async def get_order(self, order_id: int, account: str):
        return {"account": account, "id": order_id}

    async def get_pies(self, account: str):
        return [{"account": account, "id": 2}]

    async def get_pie(self, pie_id: int, account: str):
        return {"account": account, "id": pie_id}

    async def get_dividends(self, account: str):
        return [{"account": account, "ticker": "AAPL_US_EQ"}]

    async def get_exchanges(self, account: str):
        return [{"account": account, "id": "NYSE"}]

    async def get_instrument_tickers(self, account: str):
        return ["AAPL_US_EQ"]

    async def get_instrument_by_ticker(self, ticker: str, account: str):
        return {"account": account, "ticker": ticker}


@pytest.mark.asyncio
async def test_registered_resources_call_wrappers():
    mcp = FakeMCP()
    register_resources(mcp, FakeReadService())
    resources = {entry.name: entry.fn for entry in mcp.resources}

    assert json.loads(await resources["trading212://accounts/{account}/info"]("isa"))["data"] == {"account": "isa"}
    assert json.loads(await resources["trading212://accounts/{account}/balance"]("isa"))["data"]["free"] == 100
    assert json.loads(await resources["trading212://accounts/{account}/portfolio"]("isa"))["data"][0]["ticker"] == "AAPL_US_EQ"
    assert (
        json.loads(await resources["trading212://accounts/{account}/portfolio/{ticker}"]("isa", "MSFT_US_EQ"))["data"]["ticker"]
        == "MSFT_US_EQ"
    )
    assert json.loads(await resources["trading212://accounts/{account}/orders"]("isa"))["data"][0]["id"] == 1
    assert json.loads(await resources["trading212://accounts/{account}/orders/{order_id}"]("isa", 7))["data"]["id"] == 7
    assert json.loads(await resources["trading212://accounts/{account}/pies"]("isa"))["data"][0]["id"] == 2
    assert json.loads(await resources["trading212://accounts/{account}/pies/{pie_id}"]("isa", 9))["data"]["id"] == 9
    assert json.loads(await resources["trading212://accounts/{account}/dividends"]("isa"))["data"][0]["ticker"] == "AAPL_US_EQ"
    assert (
        json.loads(await resources["trading212://accounts/{account}/metadata/exchanges"]("isa"))["data"][0]["id"] == "NYSE"
    )
    assert (
        json.loads(await resources["trading212://accounts/{account}/metadata/instruments/tickers"]("isa"))["data"]
        == ["AAPL_US_EQ"]
    )
    assert (
        json.loads(await resources["trading212://accounts/{account}/metadata/instruments/{ticker}"]("isa", "AAPL_US_EQ"))["data"][
            "ticker"
        ]
        == "AAPL_US_EQ"
    )
