import json

import pytest

from server.resources import resource_account_balance, resource_account_info, resource_portfolio
from server.tools import register_tools
from tests.helpers import FakeMCP


class FakeReadService:
    async def get_account_info(self):
        return {"id": "abc"}

    async def get_balance(self):
        return {"free": 100}

    async def get_portfolio(self):
        return [{"ticker": "AAPL_US_EQ"}]

    async def get_portfolio_entry(self, ticker: str):
        return {"ticker": ticker}

    async def get_instruments(self):
        return [{"ticker": "AAPL_US_EQ"}]

    async def get_instrument_tickers(self):
        return ["AAPL_US_EQ"]

    async def get_exchanges(self):
        return [{"id": "NYSE"}]

    async def get_dividends(self):
        return [{"ticker": "AAPL_US_EQ"}]

    async def get_pies(self):
        return [{"id": 1}]

    async def get_pie(self, pie_id: int):
        return {"id": pie_id}

    async def get_orders(self):
        return [{"id": 5}]

    async def get_order(self, order_id: int):
        return {"id": order_id}


class DummyClient:
    async def place_market_order(self, *args, **kwargs):
        return {}

    async def place_limit_order(self, *args, **kwargs):
        return {}

    async def place_stop_order(self, *args, **kwargs):
        return {}

    async def place_stop_limit_order(self, *args, **kwargs):
        return {}

    async def cancel_order(self, *args, **kwargs):
        return True

    async def create_pie(self, *args, **kwargs):
        return {}

    async def update_pie(self, *args, **kwargs):
        return {}

    async def delete_pie(self, *args, **kwargs):
        return True


@pytest.mark.asyncio
async def test_deprecated_read_tools_match_resource_data_payloads():
    mcp = FakeMCP()
    read_service = FakeReadService()
    register_tools(mcp, DummyClient(), read_service)

    tools = {entry.name: entry for entry in mcp.tools}

    tool_info_data = json.loads(await tools["get_account_info"].fn())
    tool_balance_data = json.loads(await tools["get_balance"].fn())
    tool_portfolio_data = json.loads(await tools["get_portfolio"].fn())

    resource_info_data = json.loads(await resource_account_info(read_service))["data"]
    resource_balance_data = json.loads(await resource_account_balance(read_service))["data"]
    resource_portfolio_data = json.loads(await resource_portfolio(read_service))["data"]

    assert tool_info_data == resource_info_data
    assert tool_balance_data == resource_balance_data
    assert tool_portfolio_data == resource_portfolio_data


def test_deprecated_read_tools_have_deprecation_metadata():
    mcp = FakeMCP()
    register_tools(mcp, DummyClient(), FakeReadService())

    deprecated_entries = [
        entry for entry in mcp.tools if entry.name.startswith("get_") and entry.meta.get("title", "").startswith("[Deprecated]")
    ]

    assert deprecated_entries
