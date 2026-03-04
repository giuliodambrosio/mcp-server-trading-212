import json
from datetime import datetime

import pytest

from server.client212 import Client212
from server.tools import (
    register_tools,
    tool_cancel_order,
    tool_create_pie,
    tool_delete_pie,
    tool_place_limit_order,
    tool_place_market_order,
    tool_place_stop_limit_order,
    tool_place_stop_order,
    tool_read_resource,
    tool_update_pie,
)
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


class FakeReadService:
    def __init__(self):
        self.default_account = "isa"
        self.client = FakeClient()

    def list_accounts(self):
        return ["isa", "invest"]

    def get_client(self, account: str):
        assert account in {"isa", "invest"}
        return self.client

    async def get_account_info(self, account: str):
        return {"id": f"{account}-id"}

    async def get_balance(self, account: str):
        return {"free": 100}

    async def get_portfolio(self, account: str):
        return [{"ticker": "AAPL_US_EQ"}]

    async def get_portfolio_entry(self, ticker: str, account: str):
        return {"ticker": ticker, "account": account}

    async def get_orders(self, account: str):
        return [{"id": 1}]

    async def get_order(self, order_id: int, account: str):
        return {"id": order_id}

    async def get_pies(self, account: str):
        return [{"id": 7}]

    async def get_pie(self, pie_id: int, account: str):
        return {"id": pie_id}

    async def get_dividends(self, account: str):
        return []

    async def get_exchanges(self, account: str):
        return []

    async def get_instrument_tickers(self, account: str):
        return ["AAPL_US_EQ"]

    async def get_instrument_by_ticker(self, ticker: str, account: str):
        return {"ticker": ticker}


@pytest.mark.asyncio
async def test_market_limit_stop_tools_call_client():
    read_service = FakeReadService()

    market = json.loads(await tool_place_market_order(read_service, "isa", "AAPL_US_EQ", 1.0, False))
    limit = json.loads(await tool_place_limit_order(read_service, "isa", "AAPL_US_EQ", 1.0, 100.5, "DAY"))
    stop = json.loads(await tool_place_stop_order(read_service, "isa", "AAPL_US_EQ", 1.0, 90.5, "GOOD_TILL_CANCEL"))
    stop_limit = json.loads(
        await tool_place_stop_limit_order(read_service, "isa", "AAPL_US_EQ", 1.0, 90.5, 89.5, "DAY")
    )

    assert market == {"ok": True}
    assert limit == {"id": 1}
    assert stop == {"id": 2}
    assert stop_limit == {"id": 3}


@pytest.mark.asyncio
async def test_cancel_and_delete_have_deterministic_messages():
    read_service = FakeReadService()

    cancel = await tool_cancel_order(read_service, "isa", 55)
    deleted = await tool_delete_pie(read_service, "isa", 77)

    assert cancel == "Order with ID 55 cancelled."
    assert deleted == "Pie with ID 77 deleted."


@pytest.mark.asyncio
async def test_create_update_pie_support_cash_alias_and_reinvest():
    read_service = FakeReadService()
    end_date = datetime(2025, 1, 1)

    created = json.loads(
        await tool_create_pie(read_service, "isa", "Growth", "CASH", {"AAPL_US_EQ": 1.0}, end_date, 1000.0)
    )
    updated = json.loads(
        await tool_update_pie(read_service, "isa", 2, "Growth", "REINVEST", {"AAPL_US_EQ": 1.0}, end_date, 1200.0)
    )

    assert created == {"pieId": 5}
    assert updated == {"pieId": 2}
    create_call = [c for c in read_service.client.calls if c[0] == "create_pie"][0]
    update_call = [c for c in read_service.client.calls if c[0] == "update_pie"][0]
    assert create_call[2] == Client212.DividendDestination.TO_ACCOUNT_CASH
    assert update_call[3] == Client212.DividendDestination.REINVEST


@pytest.mark.asyncio
async def test_read_resource_tool_supports_account_scoped_uris():
    read_service = FakeReadService()
    info = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/info"))
    balance = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/balance"))
    concrete = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/portfolio"))
    orders = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/orders"))
    pies = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/pies"))
    dividends = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/dividends"))
    exchanges = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/metadata/exchanges"))
    instrument_tickers = json.loads(
        await tool_read_resource(read_service, "trading212://accounts/isa/metadata/instruments/tickers")
    )
    templated = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/portfolio/AAPL_US_EQ"))
    order = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/orders/42"))
    pie = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/pies/7"))
    instrument = json.loads(
        await tool_read_resource(read_service, "trading212://accounts/isa/metadata/instruments/AAPL_US_EQ")
    )

    assert info["data"] == {"id": "isa-id"}
    assert balance["data"] == {"free": 100}
    assert concrete["data"] == [{"ticker": "AAPL_US_EQ"}]
    assert orders["data"] == [{"id": 1}]
    assert pies["data"] == [{"id": 7}]
    assert dividends["data"] == []
    assert exchanges["data"] == []
    assert instrument_tickers["data"] == ["AAPL_US_EQ"]
    assert templated["data"] == {"ticker": "AAPL_US_EQ", "account": "isa"}
    assert order["data"] == {"id": 42}
    assert pie["data"] == {"id": 7}
    assert instrument["data"] == {"ticker": "AAPL_US_EQ"}


@pytest.mark.asyncio
async def test_read_resource_tool_supports_account_alias_uris():
    read_service = FakeReadService()
    overview = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/account/overview"))
    info_alias = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/account/info"))
    balance_alias = json.loads(await tool_read_resource(read_service, "trading212://accounts/isa/account/balance"))

    assert overview["data"] == {"id": "isa-id"}
    assert info_alias["data"] == {"id": "isa-id"}
    assert balance_alias["data"] == {"free": 100}


@pytest.mark.asyncio
async def test_mcp_capabilities_reports_tools_resources_and_accounts():
    mcp = FakeMCP()
    read_service = FakeReadService()
    register_tools(mcp, read_service)
    tools = {entry.name: entry for entry in mcp.tools}

    async def list_tools():
        class T:
            def __init__(self, name):
                self.name = name

        return [T(name) for name in tools.keys()]

    async def list_resources():
        class R:
            def __init__(self, uri):
                self.uri = uri

        return [R("trading212://accounts/isa/info")]

    mcp.list_tools = list_tools
    mcp.list_resources = list_resources

    payload = json.loads(await tools["mcp_capabilities"].fn())
    assert "mcp_capabilities" in payload["tools"]
    assert "trading212://accounts/isa/info" in payload["resources"]
    assert "trading212://accounts/{account}/info" in payload["declared_resources"]
    assert payload["accounts"] == ["isa", "invest"]
    assert payload["default_account"] == "isa"


@pytest.mark.asyncio
async def test_mcp_capabilities_stringifies_non_json_uri_objects():
    mcp = FakeMCP()
    read_service = FakeReadService()
    register_tools(mcp, read_service)
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
        return [ResourceObj(URLLike("trading212://accounts/isa/info"))]

    mcp.list_tools = list_tools
    mcp.list_resources = list_resources

    payload = json.loads(await tools["mcp_capabilities"].fn())
    assert payload["resources"] == ["trading212://accounts/isa/info"]
    assert "trading212://accounts/{account}/portfolio/{ticker}" in payload["declared_resources"]


@pytest.mark.asyncio
async def test_registered_tool_wrappers_delegate_to_implementations():
    mcp = FakeMCP()
    read_service = FakeReadService()
    register_tools(mcp, read_service)
    tools = {entry.name: entry for entry in mcp.tools}

    list_accounts_payload = json.loads(await tools["list_accounts"].fn())
    assert list_accounts_payload == {"accounts": ["isa", "invest"], "default_account": "isa"}

    read_payload = json.loads(await tools["read_resource"].fn("trading212://accounts/isa/info"))
    assert read_payload["data"] == {"id": "isa-id"}

    market_payload = json.loads(await tools["place_market_order"].fn("isa", "AAPL_US_EQ", 1.0, False))
    limit_payload = json.loads(await tools["place_limit_order"].fn("isa", "AAPL_US_EQ", 1.0, 100.0, "DAY"))
    stop_payload = json.loads(await tools["place_stop_order"].fn("isa", "AAPL_US_EQ", 1.0, 90.0, "DAY"))
    stop_limit_payload = json.loads(
        await tools["place_stop_limit_order"].fn("isa", "AAPL_US_EQ", 1.0, 90.0, 89.0, "GOOD_TILL_CANCEL")
    )
    cancel_payload = await tools["cancel_order"].fn("isa", 99)
    create_payload = json.loads(await tools["create_pie"].fn("isa", "Growth", "CASH", {"AAPL_US_EQ": 1.0}))
    update_payload = json.loads(await tools["update_pie"].fn("isa", 7, "Growth", "REINVEST", {"AAPL_US_EQ": 1.0}))
    delete_payload = await tools["delete_pie"].fn("isa", 7)

    assert market_payload == {"ok": True}
    assert limit_payload == {"id": 1}
    assert stop_payload == {"id": 2}
    assert stop_limit_payload == {"id": 3}
    assert cancel_payload == "Order with ID 99 cancelled."
    assert create_payload == {"pieId": 5}
    assert update_payload == {"pieId": 7}
    assert delete_payload == "Pie with ID 7 deleted."
