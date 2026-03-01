from server.resources import register_resources
from server.tools import register_tools
from tests.helpers import FakeMCP


class DummyReadService:
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

    async def get_instruments(self):
        return []

    async def get_instrument_by_ticker(self, ticker: str):
        return {"ticker": ticker}


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


def test_resource_and_tool_registration_surface():
    mcp = FakeMCP()
    read_service = DummyReadService()
    client = DummyClient()

    register_resources(mcp, read_service)
    register_tools(mcp, client, read_service)

    resource_uris = {entry.name for entry in mcp.resources}
    expected_resources = {
        "trading212://account/info",
        "trading212://account/balance",
        "trading212://portfolio",
        "trading212://portfolio/{ticker}",
        "trading212://orders",
        "trading212://orders/{order_id}",
        "trading212://pies",
        "trading212://pies/{pie_id}",
        "trading212://dividends",
        "trading212://metadata/exchanges",
        "trading212://metadata/instruments/tickers",
        "trading212://metadata/instruments/{ticker}",
    }

    assert resource_uris == expected_resources

    tool_names = {entry.name for entry in mcp.tools}

    assert "place_market_order" in tool_names
    assert "mcp_capabilities" in tool_names
    assert "read_resource" in tool_names
    assert "create_pie" in tool_names
    assert "get_balance" in tool_names
    assert "get_order" in tool_names
    assert "search_portfolio_entry" not in tool_names
