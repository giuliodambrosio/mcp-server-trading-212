from __future__ import annotations

from typing import Any

from server.client212 import Client212
from server.errors import ResourceNotFoundError


class ReadService:
    """Shared read-only access layer for resources and deprecated read tools."""

    def __init__(self, clients: dict[str, Client212], default_account: str):
        if not clients:
            raise ValueError("At least one account client is required")
        if default_account not in clients:
            raise ValueError("default_account must exist in clients")
        self.clients = clients
        self.default_account = default_account

    def list_accounts(self) -> list[str]:
        return list(self.clients.keys())

    def get_client(self, account: str | None = None) -> Client212:
        key = account or self.default_account
        client = self.clients.get(key)
        if client is None:
            raise ResourceNotFoundError("account", key)
        return client

    async def get_account_info(self, account: str | None = None) -> Any:
        return await self.get_client(account).get_account_info()

    async def get_balance(self, account: str | None = None) -> Any:
        return await self.get_client(account).get_balance()

    async def get_portfolio(self, account: str | None = None) -> Any:
        return await self.get_client(account).get_portfolio()

    async def get_portfolio_entry(self, ticker: str, account: str | None = None) -> Any:
        return await self.get_client(account).get_portfolio_entry(ticker)

    async def get_orders(self, account: str | None = None) -> Any:
        return await self.get_client(account).get_orders()

    async def get_order(self, order_id: int, account: str | None = None) -> Any:
        return await self.get_client(account).get_order(order_id)

    async def get_pies(self, account: str | None = None) -> Any:
        return await self.get_client(account).get_pies()

    async def get_pie(self, pie_id: int, account: str | None = None) -> Any:
        return await self.get_client(account).get_pie(pie_id)

    async def get_dividends(self, account: str | None = None) -> Any:
        return await self.get_client(account).get_paid_dividends()

    async def get_exchanges(self, account: str | None = None) -> Any:
        return await self.get_client(account).get_exchanges()

    async def get_instruments(self, account: str | None = None) -> Any:
        return await self.get_client(account).get_instruments()

    async def get_instrument_tickers(self, account: str | None = None) -> list[str]:
        instruments = await self.get_client(account).get_instruments()
        return [instrument["ticker"] for instrument in instruments]

    async def get_instrument_by_ticker(self, ticker: str, account: str | None = None) -> dict[str, Any]:
        instruments = await self.get_client(account).get_instruments()
        for instrument in instruments:
            if instrument.get("ticker") == ticker:
                return instrument
        raise ResourceNotFoundError("instrument", ticker)
