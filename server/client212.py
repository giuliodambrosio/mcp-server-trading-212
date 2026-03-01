from __future__ import annotations

import asyncio
import base64
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable

import httpx
from httpx import Response

from server.errors import Trading212APIError


@dataclass(slots=True)
class RateLimit:
    limit: int = 0
    period: int = 0
    remaining: int = 0
    reset: int = 0
    used: int = 0

    async def wait_if_needed(self) -> None:
        if self.reset and self.remaining == 0:
            wait_time = self.reset - int(time.time())
            if wait_time > 0:
                await asyncio.sleep(wait_time + 1)

    @staticmethod
    def from_headers(headers: httpx.Headers) -> "RateLimit":
        return RateLimit(
            limit=int(headers.get("x-ratelimit-limit", 0)),
            period=int(headers.get("x-ratelimit-period", 0)),
            remaining=int(headers.get("x-ratelimit-remaining", 0)),
            reset=int(headers.get("x-ratelimit-reset", 0)),
            used=int(headers.get("x-ratelimit-used", 0)),
        )


class Client212:
    """Client for Trading212 with Basic Auth credential generation."""

    class TimeValidity(Enum):
        DAY = "DAY"
        GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"

    class DividendDestination(Enum):
        REINVEST = "REINVEST"
        TO_ACCOUNT_CASH = "TO_ACCOUNT_CASH"

    def __init__(self, key_id: str, key_secret: str, base_url: str):
        if not key_id or not key_secret or not base_url:
            raise ValueError("212_API_KEY_ID, 212_API_KEY_SECRET and 212_API_BASE_LIVE_URL must be set")

        self.key_id = key_id
        self.key_secret = key_secret
        self.base_url = base_url.rstrip("/")
        self.credentials = self.make_credentials(key_id, key_secret)
        self.ratelimit = RateLimit()

    @staticmethod
    def make_credentials(key_id: str, key_secret: str) -> str:
        credentials = f"{key_id}:{key_secret}".encode("utf-8")
        return base64.b64encode(credentials).decode("utf-8")

    def make_url(self, path: str) -> str:
        return f"{self.base_url}/{path}"

    def make_headers(self) -> dict[str, str]:
        return {"Authorization": f"Basic {self.credentials}"}

    async def adjust_to_rate_limits(self, request: Callable[[], Awaitable[Response]]) -> Response:
        attempts = 0
        while True:
            await self.ratelimit.wait_if_needed()
            response = await request()
            self.ratelimit = RateLimit.from_headers(response.headers)
            if response.status_code != 429 or attempts >= 3:
                return response
            attempts += 1

    @staticmethod
    def _response_payload(response: Response) -> Any:
        try:
            return response.json()
        except Exception:
            text = response.text
            return text if text else None

    def raise_on_error(self, response: Response, url: str, method: str) -> Response:
        if response.is_success:
            return response
        raise Trading212APIError(
            status_code=response.status_code,
            method=method,
            url=url,
            payload=self._response_payload(response),
        )

    async def get(self, path: str) -> Any:
        url = self.make_url(path)
        headers = self.make_headers()
        async with httpx.AsyncClient() as client:
            response = await self.adjust_to_rate_limits(lambda: client.get(url, headers=headers))
        self.raise_on_error(response, url, "GET")
        return response.json()

    async def post(self, path: str, data: dict[str, Any]) -> Any:
        url = self.make_url(path)
        headers = self.make_headers()
        async with httpx.AsyncClient() as client:
            response = await self.adjust_to_rate_limits(lambda: client.post(url, headers=headers, json=data))
        self.raise_on_error(response, url, "POST")
        return response.json()

    async def delete(self, path: str) -> bool:
        url = self.make_url(path)
        headers = self.make_headers()
        async with httpx.AsyncClient() as client:
            response = await self.adjust_to_rate_limits(lambda: client.delete(url, headers=headers))
        self.raise_on_error(response, url, "DELETE")
        return response.is_success

    async def get_balance(self) -> Any:
        return await self.get("equity/account/cash")

    async def get_account_info(self) -> Any:
        return await self.get("equity/account/info")

    async def get_portfolio(self) -> Any:
        return await self.get("equity/portfolio")

    async def get_portfolio_entry(self, ticker: str) -> Any:
        return await self.get(f"equity/portfolio/{ticker}")

    async def search_portfolio_entry(self, ticker: str) -> Any:
        return await self.post("equity/portfolio/ticker", {"ticker": ticker})

    async def get_instruments(self) -> Any:
        return await self.get("equity/metadata/instruments")

    async def get_exchanges(self) -> Any:
        return await self.get("equity/metadata/exchanges")

    async def get_paid_dividends(self) -> Any:
        return await self.get("history/dividends")

    async def get_pies(self) -> Any:
        return await self.get("equity/pies")

    async def get_pie(self, pie_id: int) -> Any:
        return await self.get(f"equity/pies/{pie_id}")

    async def get_orders(self) -> Any:
        return await self.get("equity/orders")

    async def get_order(self, order_id: int) -> Any:
        return await self.get(f"equity/orders/{order_id}")

    async def place_limit_order(self, limit_price: float, quantity: float, ticker: str, time_validity: TimeValidity) -> Any:
        return await self.post(
            "equity/orders/limit",
            {
                "limitPrice": limit_price,
                "quantity": quantity,
                "ticker": ticker,
                "timeValidity": time_validity.value,
            },
        )

    async def place_market_order(self, quantity: float, ticker: str, extended_hours: bool = False) -> Any:
        return await self.post(
            "equity/orders/market",
            {
                "quantity": quantity,
                "ticker": ticker,
                "extendedHours": extended_hours,
            },
        )

    async def place_stop_order(self, stop_price: float, quantity: float, ticker: str, time_validity: TimeValidity) -> Any:
        return await self.post(
            "equity/orders/stop",
            {
                "stopPrice": stop_price,
                "quantity": quantity,
                "ticker": ticker,
                "timeValidity": time_validity.value,
            },
        )

    async def place_stop_limit_order(
        self,
        stop_price: float,
        limit_price: float,
        quantity: float,
        ticker: str,
        time_validity: TimeValidity,
    ) -> Any:
        return await self.post(
            "equity/orders/stop-limit",
            {
                "stopPrice": stop_price,
                "limitPrice": limit_price,
                "quantity": quantity,
                "ticker": ticker,
                "timeValidity": time_validity.value,
            },
        )

    async def cancel_order(self, order_id: int) -> bool:
        return await self.delete(f"equity/orders/{order_id}")

    async def create_pie(
        self,
        name: str,
        dividend_destination: DividendDestination,
        instrument_shares: dict[str, float],
        end_date: datetime | None = None,
        goal: float | None = None,
    ) -> Any:
        payload = {
            "name": name,
            "goal": goal,
            "endDate": None if end_date is None else (end_date.isoformat() + "Z") if end_date.tzinfo is None else end_date.isoformat(),
            "dividendCashAction": dividend_destination.value,
            "instrumentShares": instrument_shares,
        }
        return await self.post("equity/pies", payload)

    async def delete_pie(self, pie_id: int) -> bool:
        return await self.delete(f"equity/pies/{pie_id}")

    async def update_pie(
        self,
        pie_id: int,
        name: str,
        dividend_destination: DividendDestination,
        instrument_shares: dict[str, float],
        end_date: datetime | None = None,
        goal: float | None = None,
    ) -> Any:
        payload = {
            "name": name,
            "goal": goal,
            "endDate": None if end_date is None else (end_date.isoformat() + "Z") if end_date.tzinfo is None else end_date.isoformat(),
            "dividendCashAction": dividend_destination.value,
            "instrumentShares": instrument_shares,
        }
        return await self.post(f"equity/pies/{pie_id}", payload)
