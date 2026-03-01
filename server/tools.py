from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from server.client212 import Client212
from server.read_service import ReadService
from server.resource_registry import (
    ACCOUNT_BALANCE,
    ACCOUNT_INFO,
    CONCRETE_RESOURCE_URIS,
    DIVIDENDS,
    EXCHANGES,
    INSTRUMENT_TICKER,
    INSTRUMENT_TICKERS,
    ORDERS,
    PIES,
    PORTFOLIO,
    TEMPLATE_RESOURCE_URIS,
)
from server.resources import (
    resource_account_balance,
    resource_account_info,
    resource_dividends,
    resource_exchanges,
    resource_instrument_ticker,
    resource_instrument_tickers,
    resource_order_id,
    resource_orders,
    resource_pie_id,
    resource_pies,
    resource_portfolio,
    resource_portfolio_ticker,
)

_PORTFOLIO_TICKER_RE = re.compile(r"^trading212://portfolio/(?P<ticker>[^/]+)$")
_ORDER_ID_RE = re.compile(r"^trading212://orders/(?P<order_id>\d+)$")
_PIE_ID_RE = re.compile(r"^trading212://pies/(?P<pie_id>\d+)$")
_INSTRUMENT_TICKER_RE = re.compile(r"^trading212://metadata/instruments/(?P<ticker>[^/]+)$")


def _as_json(data: Any) -> str:
    return json.dumps(data, indent=2)


def _parse_dividend_destination(value: str) -> Client212.DividendDestination:
    normalized = value.upper()
    if normalized == "CASH":
        return Client212.DividendDestination.TO_ACCOUNT_CASH
    return Client212.DividendDestination(normalized)


async def tool_read_resource(read_service: ReadService, uri: str) -> str:
    """Compatibility bridge for clients that cannot read MCP resources directly."""
    if uri == ACCOUNT_INFO:
        return await resource_account_info(read_service)
    if uri == ACCOUNT_BALANCE:
        return await resource_account_balance(read_service)
    if uri == PORTFOLIO:
        return await resource_portfolio(read_service)
    if uri == ORDERS:
        return await resource_orders(read_service)
    if uri == PIES:
        return await resource_pies(read_service)
    if uri == DIVIDENDS:
        return await resource_dividends(read_service)
    if uri == EXCHANGES:
        return await resource_exchanges(read_service)
    if uri == INSTRUMENT_TICKERS:
        return await resource_instrument_tickers(read_service)

    portfolio_match = _PORTFOLIO_TICKER_RE.fullmatch(uri)
    if portfolio_match:
        return await resource_portfolio_ticker(read_service, portfolio_match.group("ticker"))

    order_match = _ORDER_ID_RE.fullmatch(uri)
    if order_match:
        return await resource_order_id(read_service, int(order_match.group("order_id")))

    pie_match = _PIE_ID_RE.fullmatch(uri)
    if pie_match:
        return await resource_pie_id(read_service, int(pie_match.group("pie_id")))

    instrument_match = _INSTRUMENT_TICKER_RE.fullmatch(uri)
    if instrument_match:
        return await resource_instrument_ticker(read_service, instrument_match.group("ticker"))

    raise ValueError(f"Unsupported resource URI: {uri}")


async def tool_place_market_order(client: Client212, ticker: str, quantity: float, extended_hours: bool = False) -> str:
    return _as_json(await client.place_market_order(quantity, ticker, extended_hours))


async def tool_place_limit_order(
    client: Client212,
    ticker: str,
    quantity: float,
    limit_price: float,
    time_validity: str,
) -> str:
    return _as_json(
        await client.place_limit_order(
            limit_price=limit_price,
            quantity=quantity,
            ticker=ticker,
            time_validity=Client212.TimeValidity(time_validity),
        )
    )


async def tool_place_stop_order(client: Client212, ticker: str, quantity: float, stop_price: float, time_validity: str) -> str:
    return _as_json(
        await client.place_stop_order(
            stop_price=stop_price,
            quantity=quantity,
            ticker=ticker,
            time_validity=Client212.TimeValidity(time_validity),
        )
    )


async def tool_place_stop_limit_order(
    client: Client212,
    ticker: str,
    quantity: float,
    stop_price: float,
    limit_price: float,
    time_validity: str,
) -> str:
    return _as_json(
        await client.place_stop_limit_order(
            stop_price=stop_price,
            limit_price=limit_price,
            quantity=quantity,
            ticker=ticker,
            time_validity=Client212.TimeValidity(time_validity),
        )
    )


async def tool_cancel_order(client: Client212, order_id: int) -> str:
    await client.cancel_order(order_id)
    return f"Order with ID {order_id} cancelled."


async def tool_create_pie(
    client: Client212,
    name: str,
    dividend_destination: str,
    instrument_shares: dict[str, float],
    end_date: datetime | None,
    goal: float | None,
) -> str:
    return _as_json(
        await client.create_pie(
            name=name,
            dividend_destination=_parse_dividend_destination(dividend_destination),
            instrument_shares=instrument_shares,
            end_date=end_date,
            goal=goal,
        )
    )


async def tool_update_pie(
    client: Client212,
    pie_id: int,
    name: str,
    dividend_destination: str,
    instrument_shares: dict[str, float],
    end_date: datetime | None,
    goal: float | None,
) -> str:
    return _as_json(
        await client.update_pie(
            pie_id=pie_id,
            name=name,
            dividend_destination=_parse_dividend_destination(dividend_destination),
            instrument_shares=instrument_shares,
            end_date=end_date,
            goal=goal,
        )
    )


async def tool_delete_pie(client: Client212, pie_id: int) -> str:
    await client.delete_pie(pie_id)
    return f"Pie with ID {pie_id} deleted."


def register_tools(mcp: Any, client: Client212, read_service: ReadService) -> None:
    @mcp.tool(
        title="MCP capabilities",
        description="Diagnostic: returns registered tools, concrete resources, and resource templates.",
    )
    async def mcp_capabilities() -> str:
        tools = await mcp.list_tools()
        resources = await mcp.list_resources()
        payload = {
            "tools": [getattr(tool, "name", None) for tool in tools],
            "declared_resources": list(CONCRETE_RESOURCE_URIS),
            "declared_resource_templates": list(TEMPLATE_RESOURCE_URIS),
            "resources": [
                None if getattr(resource, "uri", None) is None else str(getattr(resource, "uri", None))
                for resource in resources
            ],
            "resource_templates": list(TEMPLATE_RESOURCE_URIS),
        }
        return _as_json(payload)

    @mcp.tool(
        title="Read resource URI",
        description="Compatibility bridge for clients that cannot call MCP resources directly. Pass a trading212:// URI.",
    )
    async def read_resource(uri: str) -> str:
        return await tool_read_resource(read_service, uri)

    # Mutating tools
    @mcp.tool(title="Place market order")
    async def place_market_order(ticker: str, quantity: float, extended_hours: bool = False) -> str:
        return await tool_place_market_order(client, ticker, quantity, extended_hours)

    @mcp.tool(title="Place limit order")
    async def place_limit_order(ticker: str, quantity: float, limit_price: float, time_validity: str) -> str:
        return await tool_place_limit_order(client, ticker, quantity, limit_price, time_validity)

    @mcp.tool(title="Place stop order")
    async def place_stop_order(ticker: str, quantity: float, stop_price: float, time_validity: str) -> str:
        return await tool_place_stop_order(client, ticker, quantity, stop_price, time_validity)

    @mcp.tool(title="Place stop-limit order")
    async def place_stop_limit_order(
        ticker: str,
        quantity: float,
        stop_price: float,
        limit_price: float,
        time_validity: str,
    ) -> str:
        return await tool_place_stop_limit_order(client, ticker, quantity, stop_price, limit_price, time_validity)

    @mcp.tool(title="Cancel order")
    async def cancel_order(order_id: int) -> str:
        return await tool_cancel_order(client, order_id)

    @mcp.tool(title="Create new pie")
    async def create_pie(
        name: str,
        dividend_destination: str,
        instrument_shares: dict[str, float],
        end_date: datetime | None = None,
        goal: float | None = None,
    ) -> str:
        return await tool_create_pie(client, name, dividend_destination, instrument_shares, end_date, goal)

    @mcp.tool(title="Update existing pie")
    async def update_pie(
        pie_id: int,
        name: str,
        dividend_destination: str,
        instrument_shares: dict[str, float],
        end_date: datetime | None = None,
        goal: float | None = None,
    ) -> str:
        return await tool_update_pie(client, pie_id, name, dividend_destination, instrument_shares, end_date, goal)

    @mcp.tool(title="Delete pie")
    async def delete_pie(pie_id: int) -> str:
        return await tool_delete_pie(client, pie_id)

    # Deprecated read-only wrappers kept for backward compatibility.
    @mcp.tool(title="[Deprecated] Get account info", description="Deprecated: use resource trading212://account/info")
    async def get_account_info() -> str:
        return _as_json(await read_service.get_account_info())

    @mcp.tool(title="[Deprecated] Get account balance", description="Deprecated: use resource trading212://account/balance")
    async def get_balance() -> str:
        return _as_json(await read_service.get_balance())

    @mcp.tool(title="[Deprecated] Get all portfolio positions", description="Deprecated: use resource trading212://portfolio")
    async def get_portfolio() -> str:
        return _as_json(await read_service.get_portfolio())

    @mcp.tool(title="[Deprecated] Get specific portfolio position", description="Deprecated: use resource trading212://portfolio/{ticker}")
    async def get_portfolio_entry(ticker: str) -> str:
        return _as_json(await read_service.get_portfolio_entry(ticker))

    @mcp.tool(title="[Deprecated] Get all available instruments", description="Deprecated: use resource trading212://metadata/instruments/{ticker}")
    async def get_instruments() -> str:
        return _as_json(await read_service.get_instruments())

    @mcp.tool(title="[Deprecated] Get instrument ticker list", description="Deprecated: use resource trading212://metadata/instruments/tickers")
    async def get_instrument_tickers() -> str:
        return _as_json(await read_service.get_instrument_tickers())

    @mcp.tool(title="[Deprecated] Get all exchanges", description="Deprecated: use resource trading212://metadata/exchanges")
    async def get_exchanges() -> str:
        return _as_json(await read_service.get_exchanges())

    @mcp.tool(title="[Deprecated] Get dividend payment history", description="Deprecated: use resource trading212://dividends")
    async def get_paid_dividends() -> str:
        return _as_json(await read_service.get_dividends())

    @mcp.tool(title="[Deprecated] Get all pies", description="Deprecated: use resource trading212://pies")
    async def get_pies() -> str:
        return _as_json(await read_service.get_pies())

    @mcp.tool(title="[Deprecated] Get detailed pie information", description="Deprecated: use resource trading212://pies/{pie_id}")
    async def get_pie(pie_id: int) -> str:
        return _as_json(await read_service.get_pie(pie_id))

    @mcp.tool(title="[Deprecated] Get all orders", description="Deprecated: use resource trading212://orders")
    async def get_orders() -> str:
        return _as_json(await read_service.get_orders())

    @mcp.tool(title="[Deprecated] Get order details", description="Deprecated: use resource trading212://orders/{order_id}")
    async def get_order(order_id: int) -> str:
        return _as_json(await read_service.get_order(order_id))
