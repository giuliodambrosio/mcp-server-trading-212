import json
from datetime import datetime

import pytest

from server.client212 import Client212
from server.tools import (
    tool_read_resource,
    tool_cancel_order,
    tool_create_pie,
    tool_delete_pie,
    tool_place_limit_order,
    tool_place_market_order,
    tool_place_stop_limit_order,
    tool_place_stop_order,
    tool_update_pie,
)
from server.tools import register_tools
from tests.helpers import FakeMCP


class FakeClient:
    def __init__(self):
        self.calls = []

    async def place_market_order(self, quantity, ticker, extended_hours=False):
        self.calls.append(("place_market_order", quantity, ticker, extended_hours))
        return {"ok": True}

    async def place_limit_order(self, limit_price, quantity, ticker, time_validity):
        self.calls.append(("place_limit_order", limit_price, quantity, ticker, time_validity))
        return {"id": 1}

    async def place_stop_order(self, stop_price, quantity, ticker, time_validity):
        self.calls.append(("place_stop_order", stop_price, quantity, ticker, time_validity))
        return {"id": 2}

    async def place_stop_limit_order(self, stop_price, limit_price, quantity, ticker, time_validity):
        self.calls.append(("place_stop_limit_order", stop_price, limit_price, quantity, ticker, time_validity))
        return {"id": 3}

    async def cancel_order(self, order_id):
        self.calls.append(("cancel_order", order_id))

    async def create_pie(self, name, dividend_destination, instrument_shares, end_date, goal):
        self.calls.append(("create_pie", name, dividend_destination, instrument_shares, end_date, goal))
        return {"pieId": 5}

    async def update_pie(self, pie_id, name, dividend_destination, instrument_shares, end_date, goal):
        self.calls.append(("update_pie", pie_id, name, dividend_destination, instrument_shares, end_date, goal))
        return {"pieId": pie_id}

    async def delete_pie(self, pie_id):
        self.calls.append(("delete_pie", pie_id))


@pytest.mark.asyncio
async def test_market_limit_stop_tools_call_client():
    client = FakeClient()

    market = json.loads(await tool_place_market_order(client, "AAPL_US_EQ", 1.0, False))
    limit = json.loads(await tool_place_limit_order(client, "AAPL_US_EQ", 1.0, 100.5, "DAY"))
    stop = json.loads(await tool_place_stop_order(client, "AAPL_US_EQ", 1.0, 90.5, "GOOD_TILL_CANCEL"))
    stop_limit = json.loads(
        await tool_place_stop_limit_order(client, "AAPL_US_EQ", 1.0, 90.5, 89.5, "DAY")
    )

    assert market == {"ok": True}
    assert limit == {"id": 1}
    assert stop == {"id": 2}
    assert stop_limit == {"id": 3}


@pytest.mark.asyncio
async def test_cancel_and_delete_have_deterministic_messages():
    client = FakeClient()

    cancel = await tool_cancel_order(client, 55)
    deleted = await tool_delete_pie(client, 77)

    assert cancel == "Order with ID 55 cancelled."
    assert deleted == "Pie with ID 77 deleted."


@pytest.mark.asyncio
async def test_create_update_pie_support_cash_alias_and_reinvest():
    client = FakeClient()
    end_date = datetime(2025, 1, 1)

    created = json.loads(await tool_create_pie(client, "Growth", "CASH", {"AAPL_US_EQ": 1.0}, end_date, 1000.0))
    updated = json.loads(
        await tool_update_pie(client, 2, "Growth", "REINVEST", {"AAPL_US_EQ": 1.0}, end_date, 1200.0)
    )

    assert created == {"pieId": 5}
    assert updated == {"pieId": 2}
    create_call = [c for c in client.calls if c[0] == "create_pie"][0]
    update_call = [c for c in client.calls if c[0] == "update_pie"][0]
    assert create_call[2] == Client212.DividendDestination.TO_ACCOUNT_CASH
    assert update_call[3] == Client212.DividendDestination.REINVEST


@pytest.mark.asyncio
async def test_read_resource_tool_supports_concrete_and_templated_uris():
    class FakeReadService:
        async def get_account_info(self):
            return {"id": "abc"}

        async def get_balance(self):
            return {"free": 100}

        async def get_portfolio(self):
            return [{"ticker": "AAPL_US_EQ"}]

        async def get_portfolio_entry(self, ticker: str):
            return {"ticker": ticker}

        async def get_orders(self):
            return [{"id": 1}]

        async def get_order(self, order_id: int):
            return {"id": order_id}

        async def get_pies(self):
            return [{"id": 7}]

        async def get_pie(self, pie_id: int):
            return {"id": pie_id}

        async def get_dividends(self):
            return []

        async def get_exchanges(self):
            return []

        async def get_instrument_tickers(self):
            return ["AAPL_US_EQ"]

        async def get_instrument_by_ticker(self, ticker: str):
            return {"ticker": ticker}

    read_service = FakeReadService()
    concrete = json.loads(await tool_read_resource(read_service, "trading212://portfolio"))
    templated = json.loads(await tool_read_resource(read_service, "trading212://portfolio/AAPL_US_EQ"))
    order = json.loads(await tool_read_resource(read_service, "trading212://orders/42"))
    pie = json.loads(await tool_read_resource(read_service, "trading212://pies/7"))
    instrument = json.loads(await tool_read_resource(read_service, "trading212://metadata/instruments/AAPL_US_EQ"))

    assert concrete["data"] == [{"ticker": "AAPL_US_EQ"}]
    assert templated["data"] == {"ticker": "AAPL_US_EQ"}
    assert order["data"] == {"id": 42}
    assert pie["data"] == {"id": 7}
    assert instrument["data"] == {"ticker": "AAPL_US_EQ"}


@pytest.mark.asyncio
async def test_mcp_capabilities_reports_tools_resources_and_templates():
    class FakeReadService:
        async def get_account_info(self):
            return {}

        async def get_balance(self):
            return {}

        async def get_portfolio(self):
            return []

        async def get_portfolio_entry(self, ticker: str):
            return {"ticker": ticker}

        async def get_orders(self):
            return []

        async def get_order(self, order_id: int):
            return {"id": order_id}

        async def get_pies(self):
            return []

        async def get_pie(self, pie_id: int):
            return {"id": pie_id}

        async def get_dividends(self):
            return []

        async def get_exchanges(self):
            return []

        async def get_instrument_tickers(self):
            return []

        async def get_instrument_by_ticker(self, ticker: str):
            return {"ticker": ticker}

        async def get_instruments(self):
            return []

    mcp = FakeMCP()
    register_tools(mcp, FakeClient(), FakeReadService())
    tools = {entry.name: entry for entry in mcp.tools}

    # FakeMCP does not implement list_tools/list_resources; attach lightweight stubs.
    async def list_tools():
        class T:
            def __init__(self, name):
                self.name = name

        return [T(name) for name in tools.keys()]

    async def list_resources():
        class R:
            def __init__(self, uri):
                self.uri = uri

        return [R("trading212://account/info")]

    mcp.list_tools = list_tools
    mcp.list_resources = list_resources

    payload = json.loads(await tools["mcp_capabilities"].fn())
    assert "mcp_capabilities" in payload["tools"]
    assert "trading212://account/info" in payload["resources"]
    assert "trading212://account/info" in payload["declared_resources"]
    assert "trading212://portfolio/{ticker}" in payload["resource_templates"]
    assert "trading212://portfolio/{ticker}" in payload["declared_resource_templates"]


@pytest.mark.asyncio
async def test_mcp_capabilities_stringifies_non_json_uri_objects():
    mcp = FakeMCP()
    register_tools(mcp, FakeClient(), object())
    tools = {entry.name: entry for entry in mcp.tools}

    class URLLike:
        def __init__(self, value: str):
            self.value = value

        def __str__(self) -> str:
            return self.value

    class ToolObj:
        def __init__(self, name: str):
            self.name = name

    class ResourceObj:
        def __init__(self, uri):
            self.uri = uri

    async def list_tools():
        return [ToolObj("mcp_capabilities")]

    async def list_resources():
        return [ResourceObj(URLLike("trading212://account/info"))]

    mcp.list_tools = list_tools
    mcp.list_resources = list_resources

    payload = json.loads(await tools["mcp_capabilities"].fn())
    assert payload["resources"] == ["trading212://account/info"]
    assert "trading212://portfolio/{ticker}" in payload["resource_templates"]
