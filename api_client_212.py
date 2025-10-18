import base64
import json
import time
from datetime import datetime
from enum import Enum
from typing import Optional, Callable, Awaitable

import dotenv
import httpx
from httpx import Response


class RateLimit:
    def __init__(self, limit=None, period=None, remaining=None, reset=None, used=None):
        self.limit = limit
        self.period = period
        self.remaining = remaining
        self.reset = reset
        self.used = used
        self.color_yellow = "\033[93m"
        self.color_reset = "\033[0m"
        self.color = self.color_yellow

    def __repr__(self):
        return f"RateLimit(limit={self.limit}, period={self.period}, remaining={self.remaining}, reset={self.reset}, used={self.used})"

    def ensure_can_call(self):
        if self.reset and self.remaining == 0:
            wait_time = self.reset - time.time()
            if wait_time > 0:
                # print(f"{self.color}rate limit exceeded. Waiting for {round(wait_time, 1)} seconds until reset.{self.color_reset}")
                time.sleep(wait_time + 1)  # Sleep until reset plus a buffer

    @staticmethod
    def from_headers(headers):
        limits = RateLimit(
            limit=int(headers.get('x-ratelimit-limit', 0)),
            period=int(headers.get('x-ratelimit-period', 0)),
            remaining=int(headers.get('x-ratelimit-remaining', 0)),
            reset=int(headers.get('x-ratelimit-reset', 0)),
            used=int(headers.get('x-ratelimit-used', 0)),
        )
        #        print(f"{self.color}updated RateLimit from headers: {limits}{self.color_reset}")
        return limits


class Client212:
    """Client for 212 service with Basic Auth credentials generation."""

    class TimeValidity(Enum):
        DAY = "DAY"
        GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"

    class DividendDestination(Enum):
        REINVEST = "REINVEST"
        TO_ACCOUNT_CASH = "TO_ACCOUNT_CASH"

    def __init__(self, key_id: str, key_secret: str, base_url: str):
        self.key_id = key_id
        self.key_secret = key_secret
        self.base_url = base_url.rstrip('/')
        self.credentials = self.make_credentials(key_id, key_secret)
        self.ratelimit = RateLimit()
        self.color_gray = "\033[90m"
        self.color_reset = "\033[0m"
        self.color =  self.color_gray

    @staticmethod
    def make_credentials(key_id: str, key_secret: str) -> str:
        """Generate base64 encoded credentials for HTTP Basic Auth."""
        credentials = f"{key_id}:{key_secret}"
        credentials_bytes = credentials.encode('utf-8')
        base64_bytes = base64.b64encode(credentials_bytes)
        base64_credentials = base64_bytes.decode('utf-8')
        return base64_credentials

    def make_url(self, path: str) -> str:
        url = f"{self.base_url}/{path}"
        return url

    def make_headers(self) -> dict:
        return {
            'Authorization': f'Basic {self.credentials}',
        }

    async def adjust_to_rate_limits(self, request: Callable[[], Awaitable[Response]]) -> Response:
        self.ratelimit.ensure_can_call()
        response = await request()
        self.ratelimit = RateLimit.from_headers(response.headers)
        attempt = 0
        while response.status_code == 429 and attempt < 3:
            attempt += 1
            self.ratelimit.ensure_can_call()
            response = request()
        return response

    def raise_on_error(self, response: Response, url: str, method: str, data: Optional[dict] = None):
        try:
            response.raise_for_status()
        except Exception as e:
            error = f"{self.color}-- 212 {method} {url} failed with status {response.status_code}{self.color_reset}"
            try:
                error_info = response.json()
                error = f"{error}\n{self.color}Response JSON: {json.dumps(error_info, indent=2)}{self.color_reset}"
            except Exception as json_e:
                error = f"{error}\n{self.color}Failed to parse JSON response: {json_e}\nRaw response:{response.text}{self.color_reset}"
                error = f"{error}\n{self.color}Response text: {response.text}{self.color_reset}"
            if data:
                error = f"{error}\n{self.color}Request data: {json.dumps(data, indent=2)}{self.color_reset}"
            raise Exception(error, e)
        return response

    async def get(self, path: str) -> dict:
        url = self.make_url(path)
        # print(f"{self.color}-- 212 GET  {url}{self.color_reset}")
        headers = self.make_headers()
        async with httpx.AsyncClient() as client:
            response = await self.adjust_to_rate_limits(lambda: client.get(url, headers=headers))
            self.raise_on_error(response, url, "GET")
            return response.json()

    async def post(self, path: str, data: dict) -> dict:
        url = self.make_url(path)
        # print(f"{self.color}-- 212 POST {url}{self.color_reset}")
        headers = self.make_headers()
        async with httpx.AsyncClient() as client:
            response = await self.adjust_to_rate_limits(lambda: client.post(url, headers=headers, json=data))
            self.raise_on_error(response, url, "POST", data)
            return response.json()

    async def delete(self, path: str) -> bool:
        url = self.make_url(path)
        # print(f"{self.color}-- 212 DELETE {url}{self.color_reset}")
        headers = self.make_headers()
        async with httpx.AsyncClient() as client:
            response = await self.adjust_to_rate_limits(lambda: client.delete(url, headers=headers))
            self.raise_on_error(response, url, "DELETE")
            return response.is_success

    async def get_balance(self) -> dict:
        return await self.get('equity/account/cash')

    async def get_account_info(self) -> dict:
        return await self.get('equity/account/info')

    async def get_portfolio(self) -> dict:
        return await self.get('equity/portfolio')

    async def get_portfolio_entry(self, ticker: str) -> dict:
        return await self.get(f'equity/portfolio/{ticker}')

    # This is broken: the server returns 404
    async def search_portfolio_entry(self, ticker: str) -> dict:
        return await self.post('equity/portfolio/ticker', {'ticker': ticker})

    async def get_instruments(self) -> dict:
        return await self.get('equity/metadata/instruments')

    async def get_exchanges(self) -> dict:
        return await self.get('equity/metadata/exchanges')

    async def get_paid_dividends(self) -> dict:
        return await self.get('history/dividends')

    async def get_pies(self) -> dict:
        return await self.get('equity/pies')

    async def get_pie(self, pie_id: int) -> dict:
        return await self.get(f'equity/pies/{pie_id}')

    async def get_orders(self) -> dict:
        return await self.get('equity/orders')

    async def get_order(self, order_id: int) -> dict:
        return await self.get(f'equity/orders/{order_id}')

    async def place_limit_order(self, limit_price: float, quantity: float, ticker: str, time_validity: TimeValidity) -> dict:
        return await self.post('equity/orders/limit', {
            "limitPrice": limit_price,
            "quantity": quantity,
            "ticker": ticker,
            "timeValidity": time_validity.value
        })

    async def place_market_order(self, quantity: float, ticker: str, extended_hours: bool = False) -> dict:
        return await self.post('equity/orders/market', {
            "quantity": quantity,
            "ticker": ticker,
            "extendedHours": extended_hours,
        })

    async def place_stop_order(self, stop_price: float, quantity: float, ticker: str, time_validity: TimeValidity) -> dict:
        return await self.post('equity/orders/stop', {
            "stopPrice": stop_price,
            "quantity": quantity,
            "ticker": ticker,
            "timeValidity": time_validity.value
        })

    async def place_stop_limit_order(self, stop_price: float, limit_price: float, quantity: float, ticker: str,
                             time_validity: TimeValidity) -> dict:
        return await self.post('equity/orders/stop-limit', {
            "stopPrice": stop_price,
            "limitPrice": limit_price,
            "quantity": quantity,
            "ticker": ticker,
            "timeValidity": time_validity.value
        })

    async def cancel_order(self, order_id: int):
        return await self.delete(f'equity/orders/{order_id}')

    async def create_pie(self, name: str, dividend_destination: DividendDestination, instrument_shares: dict[str, float], end_date: datetime | None = None, goal: float | None = None) -> dict:
        return await self.post('equity/pies', {
            "name": name,
            "goal": goal,
            "endDate": None if end_date is None else (end_date.isoformat() + "Z") if end_date.tzinfo is None else end_date.isoformat(),
            "dividendCashAction": dividend_destination.value,
            "instrumentShares": instrument_shares
        })

    async def delete_pie(self, pie_id: int):
        return await self.delete(f'equity/pies/{pie_id}')

    async def update_pie(self, pie_id: int, name: str, dividend_destination: DividendDestination, instrument_shares: dict[str, float], end_date: datetime | None = None, goal: float | None = None) -> dict:
        return await self.post(f'equity/pies/{pie_id}', {
            "name": name,
            "goal": goal,
            "endDate": None if end_date is None else (end_date.isoformat() + "Z") if end_date.tzinfo is None else end_date.isoformat(),
            "dividendCashAction": dividend_destination.value,
            "instrumentShares": instrument_shares
        })


if __name__ == "__main__":
    import asyncio

    async def main():
        import os
        client = Client212(os.getenv('212_API_KEY_ID'), os.getenv('212_API_KEY_SECRET'), os.getenv('212_API_BASE_LIVE_URL'))
        response = await client.get_portfolio()
        print(json.dumps(response, indent=2))

    dotenv.load_dotenv()
    asyncio.run(main())
