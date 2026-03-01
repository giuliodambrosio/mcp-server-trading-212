from __future__ import annotations

from typing import Any

from server.client212 import Client212
from server.errors import ResourceNotFoundError


class ReadService:
    """Shared read-only access layer for resources and deprecated read tools."""

    def __init__(self, client: Client212):
        self.client = client

    async def get_account_info(self) -> Any:
        return await self.client.get_account_info()

    async def get_balance(self) -> Any:
        return await self.client.get_balance()

    async def get_portfolio(self) -> Any:
        return await self.client.get_portfolio()

    async def get_portfolio_entry(self, ticker: str) -> Any:
        return await self.client.get_portfolio_entry(ticker)

    async def get_orders(self) -> Any:
        return await self.client.get_orders()

    async def get_order(self, order_id: int) -> Any:
        return await self.client.get_order(order_id)

    async def get_pies(self) -> Any:
        return await self.client.get_pies()

    async def get_pie(self, pie_id: int) -> Any:
        return await self.client.get_pie(pie_id)

    async def get_dividends(self) -> Any:
        return await self.client.get_paid_dividends()

    async def get_exchanges(self) -> Any:
        return await self.client.get_exchanges()

    async def get_instruments(self) -> Any:
        return await self.client.get_instruments()

    async def get_instrument_tickers(self) -> list[str]:
        instruments = await self.client.get_instruments()
        return [instrument["ticker"] for instrument in instruments]

    async def get_instrument_by_ticker(self, ticker: str) -> dict[str, Any]:
        instruments = await self.client.get_instruments()
        for instrument in instruments:
            if instrument.get("ticker") == ticker:
                return instrument
        raise ResourceNotFoundError("instrument", ticker)
