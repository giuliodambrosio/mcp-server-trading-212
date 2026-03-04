from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from server.read_service import ReadService
from server.resource_registry import (
    ACCOUNT_BALANCE,
    ACCOUNT_INFO,
    DIVIDENDS,
    EXCHANGES,
    INSTRUMENT_TICKER,
    INSTRUMENT_TICKERS,
    ORDER_ID,
    ORDERS,
    PIE_ID,
    PIES,
    PORTFOLIO,
    PORTFOLIO_TICKER,
)


def _envelope(data: Any, source_endpoint: str, warnings: list[str] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "data": data,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_endpoint": source_endpoint,
    }
    if warnings:
        payload["warnings"] = warnings
    return payload


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2)


async def resource_account_info(read_service: ReadService, account: str) -> str:
    return _json(_envelope(await read_service.get_account_info(account), "equity/account/info"))


async def resource_account_balance(read_service: ReadService, account: str) -> str:
    return _json(_envelope(await read_service.get_balance(account), "equity/account/cash"))


async def resource_portfolio(read_service: ReadService, account: str) -> str:
    return _json(_envelope(await read_service.get_portfolio(account), "equity/portfolio"))


async def resource_portfolio_ticker(read_service: ReadService, account: str, ticker: str) -> str:
    return _json(_envelope(await read_service.get_portfolio_entry(ticker, account), f"equity/portfolio/{ticker}"))


async def resource_orders(read_service: ReadService, account: str) -> str:
    return _json(_envelope(await read_service.get_orders(account), "equity/orders"))


async def resource_order_id(read_service: ReadService, account: str, order_id: int) -> str:
    return _json(_envelope(await read_service.get_order(order_id, account), f"equity/orders/{order_id}"))


async def resource_pies(read_service: ReadService, account: str) -> str:
    return _json(_envelope(await read_service.get_pies(account), "equity/pies"))


async def resource_pie_id(read_service: ReadService, account: str, pie_id: int) -> str:
    return _json(_envelope(await read_service.get_pie(pie_id, account), f"equity/pies/{pie_id}"))


async def resource_dividends(read_service: ReadService, account: str) -> str:
    return _json(_envelope(await read_service.get_dividends(account), "history/dividends"))


async def resource_exchanges(read_service: ReadService, account: str) -> str:
    return _json(_envelope(await read_service.get_exchanges(account), "equity/metadata/exchanges"))


async def resource_instrument_tickers(read_service: ReadService, account: str) -> str:
    return _json(_envelope(await read_service.get_instrument_tickers(account), "equity/metadata/instruments"))


async def resource_instrument_ticker(read_service: ReadService, account: str, ticker: str) -> str:
    return _json(_envelope(await read_service.get_instrument_by_ticker(ticker, account), "equity/metadata/instruments (filtered)"))


def register_resources(mcp: Any, read_service: ReadService) -> None:
    @mcp.resource(ACCOUNT_INFO)
    async def account_info(account: str) -> str:
        return await resource_account_info(read_service, account)

    @mcp.resource(ACCOUNT_BALANCE)
    async def account_balance(account: str) -> str:
        return await resource_account_balance(read_service, account)

    @mcp.resource(PORTFOLIO)
    async def portfolio(account: str) -> str:
        return await resource_portfolio(read_service, account)

    @mcp.resource(PORTFOLIO_TICKER)
    async def portfolio_ticker(account: str, ticker: str) -> str:
        return await resource_portfolio_ticker(read_service, account, ticker)

    @mcp.resource(ORDERS)
    async def orders(account: str) -> str:
        return await resource_orders(read_service, account)

    @mcp.resource(ORDER_ID)
    async def order_id(account: str, order_id: int) -> str:
        return await resource_order_id(read_service, account, order_id)

    @mcp.resource(PIES)
    async def pies(account: str) -> str:
        return await resource_pies(read_service, account)

    @mcp.resource(PIE_ID)
    async def pie_id(account: str, pie_id: int) -> str:
        return await resource_pie_id(read_service, account, pie_id)

    @mcp.resource(DIVIDENDS)
    async def dividends(account: str) -> str:
        return await resource_dividends(read_service, account)

    @mcp.resource(EXCHANGES)
    async def exchanges(account: str) -> str:
        return await resource_exchanges(read_service, account)

    @mcp.resource(INSTRUMENT_TICKERS)
    async def instrument_tickers(account: str) -> str:
        return await resource_instrument_tickers(read_service, account)

    @mcp.resource(INSTRUMENT_TICKER)
    async def instrument_ticker(account: str, ticker: str) -> str:
        return await resource_instrument_ticker(read_service, account, ticker)
