import json
import os
from datetime import datetime
from typing import Any, Awaitable
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from api_client_212 import Client212

load_dotenv()
client = Client212(os.getenv('212_API_KEY_ID'), os.getenv('212_API_KEY_SECRET'), os.getenv('212_API_BASE_LIVE_URL'))
mcp = FastMCP("212-trading",
              instructions="A tool to interact with the 212 Trading API to manage my own account. Prices are in the currency defined in account info. They're often expressed in cents. On the platform they use the concept of 'instruments' : they can be stocks, ETFs, etc. Don't try to guess the instrument tickers: instead get the full list of available ticker symbols using get_instrument_tickers or get_instrument: prefer using the first call, since the second call output can be too large. You can then get the full details for just the symbols that you need to know about")


async def represent_response(response: Awaitable[Any]) -> str:
    """Represent the API response as a string."""
    try:
        content = await response
        return json.dumps(content, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool(title="Get account info: this includes details such as account type, currency, and status")
async def get_account_info() -> str:
    """Get account info from 212 Trading API."""
    return await represent_response(client.get_account_info())


@mcp.tool(title="Get account balance: this includes available cash and total account value")
async def get_balance() -> str:
    """Get account balance from 212 Trading API."""
    return await represent_response(client.get_balance())


@mcp.tool(
    title="Get all portfolio entries: this includes all stocks and ETFs currently held in the account either as single entries or as part of pies")
async def get_portfolio() -> str:
    """Get account portfolio from 212 Trading API."""
    return await represent_response(client.get_portfolio())


@mcp.tool(
    title="Returns info about a specific portfolio entry given its ticker symbol (e.g. AAPL, MSFT, etc.). The ticker symbol needs to exist on 212 and must be part of the portfolio: this is not a search tool.")
async def get_portfolio_entry(ticker: str) -> str:
    """Get a specific portfolio entry by ticker from 212 Trading API."""
    return await represent_response(client.get_portfolio_entry(ticker))


@mcp.tool(title="Get full descriptions for all available instruments on the platform (AAPL, MSFT, etc.)")
async def get_instruments() -> str:
    """Get available instruments from 212 Trading API."""
    return await represent_response(client.get_instruments())


@mcp.tool(title="Get Instrument Tickers only: this is useful to know what stocks are available on the platform")
async def get_instrument_tickers() -> str:
    """Get a list of instrument tickers from 212 Trading API."""
    instruments = await client.get_instruments()
    tickers = [instr['ticker'] for instr in instruments]
    return json.dumps(tickers, indent=2)


@mcp.tool(
    title="This returns information about all available exchanges. An exchange is a platform that allows trading of financial instruments.")
async def get_exchanges() -> str:
    """Get available exchanges from 212 Trading API."""
    return await represent_response(client.get_exchanges())


@mcp.tool(title="Get info about all paid dividends")
async def get_paid_dividends() -> str:
    """Get paid dividends from 212 Trading API."""
    return await represent_response(client.get_paid_dividends())


@mcp.tool(title="Get all pies: pies are collections of instruments that can be managed as a single entity")
async def get_pies() -> str:
    """Get pies from 212 Trading API."""
    return await represent_response(client.get_pies())


@mcp.tool(title="Get a specific pie by its ID")
async def get_pie(pie_id: int) -> str:
    """Get a specific pie by ID from 212 Trading API."""
    return await represent_response(client.get_pie(pie_id))


@mcp.tool(title="Get all orders: this includes both open and closed orders")
async def get_orders() -> str:
    """Get all orders from 212 Trading API."""
    return await represent_response(client.get_orders())


@mcp.tool(
    title="Place an order to buy or sell a specific instrument at market price. If extended_hours is True, the order will be placed in after hours markets if the exchange is closed.")
async def place_market_order(ticker: str, quantity: float, extended_hours: bool = False) -> str:
    """Place an order on 212 Trading API."""
    return await represent_response(client.place_market_order(quantity, ticker, extended_hours))


@mcp.tool(
    title="Place a limit order to buy or sell a specific instrument at a specified price. The order time_validity parameter can have two values: DAY or GOOD_TILL_CANCEL")
async def place_limit_order(ticker: str, quantity: float, limit_price: float, time_validity: str) -> str:
    """Place a limit order on 212 Trading API."""
    return await represent_response(
        client.place_limit_order(limit_price=limit_price, quantity=quantity, ticker=ticker, time_validity=Client212.TimeValidity(time_validity)))


@mcp.tool(
    title="Place a stop order to buy or sell a specific instrument when it reaches a specified price. The order time_validity parameter can have two values: DAY or GOOD_TILL_CANCEL")
async def place_stop_order(ticker: str, quantity: float, stop_price: float, time_validity: str) -> str:
    """Place a stop order on 212 Trading API."""
    return await represent_response(
        client.place_stop_order(stop_price=stop_price, quantity=quantity, ticker=ticker, time_validity=Client212.TimeValidity(time_validity)))

@mcp.tool(
    title="Place a stop-limit order to buy or sell a specific instrument when it reaches a specified stop price, but only at a specified limit price or better. The order time_validity parameter can have two values: DAY or GOOD_TILL_CANCEL")
async def place_stop_limit_order(ticker: str, quantity: float, stop_price: float, limit_price: float,
                                 time_validity: str) -> str:
    """Place a stop-limit order on 212 Trading API."""
    return await represent_response(
        client.place_stop_limit_order(stop_price=stop_price, limit_price=limit_price, quantity=quantity, ticker=ticker, time_validity=Client212.TimeValidity(time_validity)))

@mcp.tool(title="Cancel an existing order by its ID")
async def cancel_order(order_id: int) -> str:
    """Cancel an order on 212 Trading API."""
    await client.cancel_order(order_id)
    return f"Order with ID {order_id} cancelled."


@mcp.tool(title="Get a specific order by its ID")
async def get_order(order_id: int) -> str:
    """Get a specific order by ID from 212 Trading API."""
    return await represent_response(client.get_order(order_id))


@mcp.tool(
    title="Search for a portfolio entry by its ticker symbol. This was broken the last time I checked: the server tends to return 404")
async def search_portfolio_entry(ticker: str) -> str:
    """Search for a portfolio entry by ticker from 212 Trading API."""
    return await represent_response(client.search_portfolio_entry(ticker))


@mcp.tool(title="Create a pie: a pie is a collection of instruments that can be managed as a single entity.",
          description="dividend_destination can be one of [CASH,REINVEST]. instrument_shares should be a dictionary with the ticker symbols a keys and the share percentages as values (e.g. {'AAPL': 0.5, 'MSFT': 0.5} for a pie with 50% Apple and 50% Microsoft). The sum of all the shares needs to sum up to 1.0 (100%")
async def create_pie(name: str, dividend_destination: str, instrument_shares: dict[str, float],
                     end_date: datetime | None, goal: float | None) -> str:
    """Create a pie on 212 Trading API."""
    return await represent_response(
        client.create_pie(name=name, dividend_destination=Client212.DividendDestination(dividend_destination),
                          instrument_shares=instrument_shares, end_date=end_date, goal=goal))


@mcp.tool(
    title="Update an existing pie by its ID. dividend_destination can be one of [CASH,REINVEST]. instrument_shares should be a dictionary with the ticker symbols a keys and the share percentages as values (e.g. {'AAPL': 0.5, 'MSFT': 0.5} for a pie with 50% Apple and 50% Microsoft). The sum of all the shares needs to sum up to 1.0 (100%")
async def update_pie(pie_id: int, name: str, dividend_destination: str, instrument_shares: dict[str, float],
                     end_date: datetime | None, goal: float | None) -> str:
    """Update a pie on 212 Trading API."""
    return await represent_response(client.update_pie(pie_id=pie_id, name=name,
                                                      dividend_destination=Client212.DividendDestination(dividend_destination),
                                                      instrument_shares=instrument_shares, end_date=end_date, goal=goal))


@mcp.tool(title="Delete an existing pie by its ID")
async def delete_pie(pie_id: int) -> str:
    """Delete a pie on 212 Trading API."""
    await client.delete_pie(pie_id)
    return f"Pie with ID {pie_id} deleted."


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
