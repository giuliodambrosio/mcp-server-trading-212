import json

import pytest

from server.resources import resource_portfolio, resource_portfolio_ticker


class FakeReadService:
    async def get_portfolio(self):
        return [{"ticker": "AAPL_US_EQ", "quantity": 1.2}]

    async def get_portfolio_entry(self, ticker: str):
        return {"ticker": ticker, "quantity": 0.4}


@pytest.mark.asyncio
async def test_portfolio_resource_returns_snapshot_envelope():
    payload = json.loads(await resource_portfolio(FakeReadService()))

    assert payload["data"] == [{"ticker": "AAPL_US_EQ", "quantity": 1.2}]
    assert payload["source_endpoint"] == "equity/portfolio"


@pytest.mark.asyncio
async def test_portfolio_ticker_resource_uses_ticker_in_source_endpoint():
    payload = json.loads(await resource_portfolio_ticker(FakeReadService(), "RRl_EQ"))

    assert payload["data"] == {"ticker": "RRl_EQ", "quantity": 0.4}
    assert payload["source_endpoint"] == "equity/portfolio/RRl_EQ"
