from server.resources import register_resources
from server.tools import register_tools
from tests.helpers import FakeMCP


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


class DummyReadService:
    def __init__(self):
        self.default_account = "isa"
        self._client = DummyClient()

    def list_accounts(self):
        return ["isa", "invest"]

    def get_client(self, account: str):
        assert account in {"isa", "invest"}
        return self._client

    async def get_account_info(self, account: str):
        return {}

    async def get_balance(self, account: str):
        return {}

    async def get_portfolio(self, account: str):
        return []

    async def get_portfolio_entry(self, ticker: str, account: str):
        return {"ticker": ticker}

    async def get_orders(self, account: str):
        return []

    async def get_order(self, order_id: int, account: str):
        return {"id": order_id}

    async def get_pies(self, account: str):
        return []

    async def get_pie(self, pie_id: int, account: str):
        return {"id": pie_id}

    async def get_dividends(self, account: str):
        return []

    async def get_exchanges(self, account: str):
        return []

    async def get_instrument_tickers(self, account: str):
        return []

    async def get_instrument_by_ticker(self, ticker: str, account: str):
        return {"ticker": ticker}


def test_resource_and_tool_registration_surface():
    mcp = FakeMCP()
    read_service = DummyReadService()

    register_resources(mcp, read_service)
    register_tools(mcp, read_service)

    resource_uris = {entry.name for entry in mcp.resources}
    expected_resources = {
        "trading212://accounts/{account}/info",
        "trading212://accounts/{account}/balance",
        "trading212://accounts/{account}/portfolio",
        "trading212://accounts/{account}/portfolio/{ticker}",
        "trading212://accounts/{account}/orders",
        "trading212://accounts/{account}/orders/{order_id}",
        "trading212://accounts/{account}/pies",
        "trading212://accounts/{account}/pies/{pie_id}",
        "trading212://accounts/{account}/dividends",
        "trading212://accounts/{account}/metadata/exchanges",
        "trading212://accounts/{account}/metadata/instruments/tickers",
        "trading212://accounts/{account}/metadata/instruments/{ticker}",
    }

    assert resource_uris == expected_resources

    tool_names = {entry.name for entry in mcp.tools}

    assert "place_market_order" in tool_names
    assert "mcp_capabilities" in tool_names
    assert "list_accounts" in tool_names
    assert "read_resource" in tool_names
    assert "create_pie" in tool_names
    assert "get_balance" not in tool_names
    assert "get_order" not in tool_names
    assert "search_portfolio_entry" not in tool_names
