from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from server.client212 import Client212
from server.read_service import ReadService
from server.resource_registry import RESOURCE_URIS
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

_ACCOUNT_INFO_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/info$")
_ACCOUNT_BALANCE_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/balance$")
_ACCOUNT_OVERVIEW_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/account/overview$")
_ACCOUNT_INFO_ALIAS_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/account/info$")
_ACCOUNT_BALANCE_ALIAS_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/account/balance$")
_PORTFOLIO_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/portfolio$")
_ORDERS_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/orders$")
_PIES_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/pies$")
_DIVIDENDS_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/dividends$")
_EXCHANGES_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/metadata/exchanges$")
_INSTRUMENT_TICKERS_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/metadata/instruments/tickers$")
_PORTFOLIO_TICKER_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/portfolio/(?P<ticker>[^/]+)$")
_ORDER_ID_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/orders/(?P<order_id>\d+)$")
_PIE_ID_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/pies/(?P<pie_id>\d+)$")
_INSTRUMENT_TICKER_RE = re.compile(r"^trading212://accounts/(?P<account>[^/]+)/metadata/instruments/(?P<ticker>[^/]+)$")


def _as_json(data: Any) -> str:
    return json.dumps(data, indent=2)


def _parse_dividend_destination(value: str) -> Client212.DividendDestination:
    normalized = value.upper()
    if normalized == "CASH":
        return Client212.DividendDestination.TO_ACCOUNT_CASH
    return Client212.DividendDestination(normalized)


async def tool_read_resource(read_service: ReadService, uri: str) -> str:
    """Compatibility bridge for clients that cannot read MCP resources directly."""
    if match := _ACCOUNT_INFO_RE.fullmatch(uri):
        return await resource_account_info(read_service, match.group("account"))
    if match := _ACCOUNT_BALANCE_RE.fullmatch(uri):
        return await resource_account_balance(read_service, match.group("account"))
    if match := _ACCOUNT_OVERVIEW_RE.fullmatch(uri):
        return await resource_account_info(read_service, match.group("account"))
    if match := _ACCOUNT_INFO_ALIAS_RE.fullmatch(uri):
        return await resource_account_info(read_service, match.group("account"))
    if match := _ACCOUNT_BALANCE_ALIAS_RE.fullmatch(uri):
        return await resource_account_balance(read_service, match.group("account"))
    if match := _PORTFOLIO_RE.fullmatch(uri):
        return await resource_portfolio(read_service, match.group("account"))
    if match := _ORDERS_RE.fullmatch(uri):
        return await resource_orders(read_service, match.group("account"))
    if match := _PIES_RE.fullmatch(uri):
        return await resource_pies(read_service, match.group("account"))
    if match := _DIVIDENDS_RE.fullmatch(uri):
        return await resource_dividends(read_service, match.group("account"))
    if match := _EXCHANGES_RE.fullmatch(uri):
        return await resource_exchanges(read_service, match.group("account"))
    if match := _INSTRUMENT_TICKERS_RE.fullmatch(uri):
        return await resource_instrument_tickers(read_service, match.group("account"))
    if match := _PORTFOLIO_TICKER_RE.fullmatch(uri):
        return await resource_portfolio_ticker(read_service, match.group("account"), match.group("ticker"))
    if match := _ORDER_ID_RE.fullmatch(uri):
        return await resource_order_id(read_service, match.group("account"), int(match.group("order_id")))
    if match := _PIE_ID_RE.fullmatch(uri):
        return await resource_pie_id(read_service, match.group("account"), int(match.group("pie_id")))
    if match := _INSTRUMENT_TICKER_RE.fullmatch(uri):
        return await resource_instrument_ticker(read_service, match.group("account"), match.group("ticker"))

    raise ValueError(f"Unsupported resource URI: {uri}")


async def tool_place_market_order(
    read_service: ReadService,
    account: str,
    ticker: str,
    quantity: float,
    extended_hours: bool = False,
) -> str:
    client = read_service.get_client(account)
    return _as_json(await client.place_market_order(quantity, ticker, extended_hours))


async def tool_place_limit_order(
    read_service: ReadService,
    account: str,
    ticker: str,
    quantity: float,
    limit_price: float,
    time_validity: str,
) -> str:
    client = read_service.get_client(account)
    return _as_json(
        await client.place_limit_order(
            limit_price=limit_price,
            quantity=quantity,
            ticker=ticker,
            time_validity=Client212.TimeValidity(time_validity),
        )
    )


async def tool_place_stop_order(
    read_service: ReadService,
    account: str,
    ticker: str,
    quantity: float,
    stop_price: float,
    time_validity: str,
) -> str:
    client = read_service.get_client(account)
    return _as_json(
        await client.place_stop_order(
            stop_price=stop_price,
            quantity=quantity,
            ticker=ticker,
            time_validity=Client212.TimeValidity(time_validity),
        )
    )


async def tool_place_stop_limit_order(
    read_service: ReadService,
    account: str,
    ticker: str,
    quantity: float,
    stop_price: float,
    limit_price: float,
    time_validity: str,
) -> str:
    client = read_service.get_client(account)
    return _as_json(
        await client.place_stop_limit_order(
            stop_price=stop_price,
            limit_price=limit_price,
            quantity=quantity,
            ticker=ticker,
            time_validity=Client212.TimeValidity(time_validity),
        )
    )


async def tool_cancel_order(read_service: ReadService, account: str, order_id: int) -> str:
    client = read_service.get_client(account)
    await client.cancel_order(order_id)
    return f"Order with ID {order_id} cancelled."


async def tool_create_pie(
    read_service: ReadService,
    account: str,
    name: str,
    dividend_destination: str,
    instrument_shares: dict[str, float],
    end_date: datetime | None,
    goal: float | None,
) -> str:
    client = read_service.get_client(account)
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
    read_service: ReadService,
    account: str,
    pie_id: int,
    name: str,
    dividend_destination: str,
    instrument_shares: dict[str, float],
    end_date: datetime | None,
    goal: float | None,
) -> str:
    client = read_service.get_client(account)
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


async def tool_delete_pie(read_service: ReadService, account: str, pie_id: int) -> str:
    client = read_service.get_client(account)
    await client.delete_pie(pie_id)
    return f"Pie with ID {pie_id} deleted."


def register_tools(mcp: Any, read_service: ReadService) -> None:
    @mcp.tool(
        title="MCP capabilities",
        description="Diagnostic: returns registered tools, concrete resources, and resource templates.",
    )
    async def mcp_capabilities() -> str:
        tools = await mcp.list_tools()
        resources = await mcp.list_resources()
        payload = {
            "tools": [getattr(tool, "name", None) for tool in tools],
            "declared_resources": list(RESOURCE_URIS),
            "resources": [
                None if getattr(resource, "uri", None) is None else str(getattr(resource, "uri", None))
                for resource in resources
            ],
            "accounts": read_service.list_accounts(),
            "default_account": read_service.default_account,
        }
        return _as_json(payload)

    @mcp.tool(
        title="List configured accounts",
        description="Returns account aliases configured in .env and the default account.",
    )
    async def list_accounts() -> str:
        return _as_json({"accounts": read_service.list_accounts(), "default_account": read_service.default_account})

    @mcp.tool(
        title="Read resource URI",
        description=(
            "Compatibility bridge for clients that cannot call MCP resources directly. "
            "Pass a trading212://accounts/{account}/... URI."
        ),
    )
    async def read_resource(uri: str) -> str:
        return await tool_read_resource(read_service, uri)

    @mcp.tool(title="Place market order")
    async def place_market_order(account: str, ticker: str, quantity: float, extended_hours: bool = False) -> str:
        return await tool_place_market_order(read_service, account, ticker, quantity, extended_hours)

    @mcp.tool(title="Place limit order")
    async def place_limit_order(account: str, ticker: str, quantity: float, limit_price: float, time_validity: str) -> str:
        return await tool_place_limit_order(read_service, account, ticker, quantity, limit_price, time_validity)

    @mcp.tool(title="Place stop order")
    async def place_stop_order(account: str, ticker: str, quantity: float, stop_price: float, time_validity: str) -> str:
        return await tool_place_stop_order(read_service, account, ticker, quantity, stop_price, time_validity)

    @mcp.tool(title="Place stop-limit order")
    async def place_stop_limit_order(
        account: str,
        ticker: str,
        quantity: float,
        stop_price: float,
        limit_price: float,
        time_validity: str,
    ) -> str:
        return await tool_place_stop_limit_order(
            read_service, account, ticker, quantity, stop_price, limit_price, time_validity
        )

    @mcp.tool(title="Cancel order")
    async def cancel_order(account: str, order_id: int) -> str:
        return await tool_cancel_order(read_service, account, order_id)

    @mcp.tool(title="Create new pie")
    async def create_pie(
        account: str,
        name: str,
        dividend_destination: str,
        instrument_shares: dict[str, float],
        end_date: datetime | None = None,
        goal: float | None = None,
    ) -> str:
        return await tool_create_pie(read_service, account, name, dividend_destination, instrument_shares, end_date, goal)

    @mcp.tool(title="Update existing pie")
    async def update_pie(
        account: str,
        pie_id: int,
        name: str,
        dividend_destination: str,
        instrument_shares: dict[str, float],
        end_date: datetime | None = None,
        goal: float | None = None,
    ) -> str:
        return await tool_update_pie(
            read_service,
            account,
            pie_id,
            name,
            dividend_destination,
            instrument_shares,
            end_date,
            goal,
        )

    @mcp.tool(title="Delete pie")
    async def delete_pie(account: str, pie_id: int) -> str:
        return await tool_delete_pie(read_service, account, pie_id)
