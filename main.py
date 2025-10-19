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
              instructions="""
                A tool to interact with the 212 Trading API to manage my own account.
                
                CRITICAL INFORMATION ABOUT PRICES AND CURRENCIES:
                * Prices are returned in the instrument's native currency unit, which may be in SUBUNITS (pence, cents, etc.)
                * UK stocks (tickers ending in l_EQ) have prices in GBX (pence), NOT GBP. Divide by 100 to get pounds.
                * US stocks (tickers ending in _US_EQ) have prices in USD (dollars), not cents.
                * Check the instrument metadata to determine the currencyCode for each position.
                * When calculating position values, be careful to apply correct currency conversions.
                
                INSTRUMENT DEFINITIONS:
                * 'instrument': stocks, ETFs, and other tradable securities
                * Don't guess ticker symbols - use get_instrument_tickers or get_instruments
                * Ticker format examples: 'AAPL_US_EQ' (not 'AAPL'), 'RRl_EQ' (UK stock)
                
                PORTFOLIO DATA FIELDS:
                * quantity: fractional number of shares held (this is a float, not int)
                * averagePrice: average purchase price in native currency unit
                * currentPrice: current market price in native currency unit
                * ppl: profit/loss in account currency (already converted)
                * fxPpl: foreign exchange profit/loss if applicable
                * pieQuantity: quantity held in pies
                * frontend: where position was opened (WEB, API, AUTOINVEST, etc.)
                * initialFillDate: when position was first opened
                
                CALCULATION NOTES:
                * To get position value: quantity × currentPrice (in native currency)
                * For UK stocks: convert GBX to GBP by dividing by 100
                * The 'ppl' field is already in account currency and properly converted
                """)


async def render_response(response: Awaitable[Any]) -> str:
    """Renders the API response as a string."""
    try:
        content = await response
        return json.dumps(content, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool(
    title="Get account info",
    description="Returns account metadata including account ID and primary currency code (e.g., 'GBP', 'USD'). This tells you what currency all monetary values are denominated in."
)
async def get_account_info() -> str:
    """Get account info from 212 Trading API."""
    return await render_response(client.get_account_info())


@mcp.tool(
    title="Get account balance",
    description="""Returns detailed account balance in the account's primary currency:
    - total: total portfolio value (cash + invested positions)
    - free: available cash for trading
    - invested: total value currently invested in positions
    - result: total profit/loss
    - ppl: unrealized profit/loss on open positions
    - pieCash: cash allocated to pies
    - blocked: cash that is blocked (e.g., pending orders)
    All values are in the account's primary currency."""
)
async def get_balance() -> str:
    """Get account balance from 212 Trading API."""
    return await render_response(client.get_balance())


@mcp.tool(
    title="Get all portfolio positions",
    description="""Returns array of all open positions (stocks/ETFs) held in the account.
    
    CRITICAL - PRICE UNITS:
    - averagePrice and currentPrice are in the instrument's NATIVE CURRENCY UNIT
    - UK stocks (ticker ending in l_EQ): prices in GBX (pence) - divide by 100 for GBP
    - US stocks (ticker ending in _US_EQ): prices in USD (dollars)
    - To get position value in native currency: quantity × currentPrice
    - For UK stocks, position value in GBP: (quantity × currentPrice) / 100
    
    Fields returned:
    - ticker: instrument identifier (e.g., 'AAPL_US_EQ', 'RRl_EQ')
    - quantity: fractional number of shares owned
    - averagePrice: avg purchase price in native currency unit
    - currentPrice: current market price in native currency unit
    - ppl: profit/loss in account currency (already properly converted)
    - fxPpl: foreign exchange P&L if applicable
    - pieQuantity: quantity held within pies
    - initialFillDate: date position was opened
    - frontend: where opened (WEB, API, AUTOINVEST, IOS, etc.)
    - maxBuy/maxSell: maximum quantities for trading"""
)
async def get_portfolio() -> str:
    """Get account portfolio from 212 Trading API."""
    return await render_response(client.get_portfolio())


@mcp.tool(
    title="Get specific portfolio position",
    description="""Returns detailed info about ONE portfolio position by ticker symbol.
    
    IMPORTANT: This only works for positions you currently hold. Not a search tool.
    
    Same price unit rules apply - see get_portfolio description for details on price units.
    Use this when you need to verify currency units or get fresh data for a specific position."""
)
async def get_portfolio_entry(ticker: str) -> str:
    """Get a specific portfolio entry by ticker from 212 Trading API."""
    return await render_response(client.get_portfolio_entry(ticker))


@mcp.tool(
    title="Get all available instruments",
    description="""Returns full metadata for ALL tradable instruments on the platform.
    
    WARNING: This returns a very large dataset. Prefer get_instrument_tickers for lighter queries.
    
    Each instrument includes:
    - ticker: unique identifier (e.g., 'AAPL_US_EQ')
    - name: full company name
    - shortName: abbreviated name
    - currencyCode: the currency prices are quoted in (USD, GBP, EUR, etc.)
    - isin: international securities ID
    - type: STOCK or ETF
    - maxOpenQuantity: maximum position size allowed
    
    CRITICAL: currencyCode tells you the currency unit. If currencyCode is 'GBX', prices are in pence."""
)
async def get_instruments() -> str:
    """Get available instruments from 212 Trading API."""
    return await render_response(client.get_instruments())


@mcp.tool(
    title="Get instrument ticker list",
    description="""Returns ONLY the ticker symbols of all available instruments. Much lighter than get_instruments.
    
    Use this to:
    - Find the correct ticker format for a stock you want to trade
    - Browse available instruments without loading full metadata
    - Search for tickers matching a pattern
    
    Remember: tickers include suffixes like '_US_EQ' or 'l_EQ'"""
)
async def get_instrument_tickers() -> str:
    """Get a list of instrument tickers from 212 Trading API."""
    instruments = await client.get_instruments()
    tickers = [instr['ticker'] for instr in instruments]
    return json.dumps(tickers, indent=2)


@mcp.tool(
    title="Get all exchanges",
    description="Returns information about all trading exchanges available, including their working schedules and trading hours."
)
async def get_exchanges() -> str:
    """Get available exchanges from 212 Trading API."""
    return await render_response(client.get_exchanges())


@mcp.tool(
    title="Get dividend payment history",
    description="""Returns all dividends paid out to the account.
    
    Each dividend includes:
    - amount: dividend amount in account currency
    - quantity: fractional number of shares that received the dividend
    - ticker: instrument that paid the dividend
    - paidOn: payment date
    - grossAmountPerShare: pre-tax dividend per share"""
)
async def get_paid_dividends() -> str:
    """Get paid dividends from 212 Trading API."""
    return await render_response(client.get_paid_dividends())


@mcp.tool(
    title="Get all pies",
    description="""Returns all investment pies (automated portfolio allocations).
    
    Pies allow you to group instruments and maintain target allocations automatically.
    Each pie includes progress, cash allocated, dividends, and performance metrics."""
)
async def get_pies() -> str:
    """Get pies from 212 Trading API."""
    return await render_response(client.get_pies())


@mcp.tool(
    title="Get detailed pie information",
    description="Returns detailed information about a specific pie including all instruments, their current/expected allocations, and performance."
)
async def get_pie(pie_id: int) -> str:
    """Get a specific pie by ID from 212 Trading API."""
    return await render_response(client.get_pie(pie_id))


@mcp.tool(
    title="Get all orders",
    description="""Returns all orders (open and historical).
    
    Includes market, limit, stop, and stop-limit orders with their status, quantities, and prices."""
)
async def get_orders() -> str:
    """Get all orders from 212 Trading API."""
    return await render_response(client.get_orders())


@mcp.tool(
    title="Place market order",
    description="""Place an order at current market price. Executes immediately during market hours.
    
    Parameters:
    - ticker: instrument ticker (e.g., 'AAPL_US_EQ')
    - quantity (float): fractional number of shares. Positive for buy, negative for sell
    - extended_hours: if True, allows trading outside regular hours (demo only)
    
    LIVE ACCOUNT LIMITATION: Only market orders are supported in live trading via API."""
)
async def place_market_order(ticker: str, quantity: float, extended_hours: bool = False) -> str:
    """Place an order on 212 Trading API."""
    return await render_response(client.place_market_order(quantity, ticker, extended_hours))


@mcp.tool(
    title="Place limit order",
    description="""Place an order that executes only at specified price or better.
    
    Parameters:
    - ticker: instrument ticker
    - quantity (float): fractional number of shares. Positive for buy, negative for sell
    - limit_price (float): maximum price for buy / minimum price for sell
    - time_validity: 'DAY' (expires end of day) or 'GOOD_TILL_CANCEL'
    
    NOTE: Only available in demo accounts. Live accounts only support market orders."""
)
async def place_limit_order(ticker: str, quantity: float, limit_price: float, time_validity: str) -> str:
    """Place a limit order on 212 Trading API."""
    return await render_response(
        client.place_limit_order(limit_price=limit_price, quantity=quantity, ticker=ticker, time_validity=Client212.TimeValidity(time_validity)))


@mcp.tool(
    title="Place stop order",
    description="""Place a stop order (becomes market order when stop price reached).
    
    Commonly used for stop-loss protection. Triggers when last traded price hits stopPrice.
    
    Parameters:
    - ticker: instrument ticker
    - quantity (float): fractional number of shares. Positive for buy stop, negative for sell stop (stop-loss)
    - stop_price (float): trigger price
    - time_validity: 'DAY' or 'GOOD_TILL_CANCEL'
    
    NOTE: Only available in demo accounts."""
)
async def place_stop_order(ticker: str, quantity: float, stop_price: float, time_validity: str) -> str:
    """Place a stop order on 212 Trading API."""
    return await render_response(
        client.place_stop_order(stop_price=stop_price, quantity=quantity, ticker=ticker, time_validity=Client212.TimeValidity(time_validity)))

@mcp.tool(
    title="Place stop-limit order",
    description="""Place a stop-limit order (becomes limit order when stop price reached).
    
    Combines stop and limit: triggers at stopPrice, then places limit order at limitPrice.
    Protects against slippage better than regular stop orders.
    
    Parameters:
    - ticker: instrument ticker
    - quantity (float): fractional number of shares. Positive for buy, negative for sell
    - stop_price (float): trigger price
    - limit_price (float): limit price once triggered
    - time_validity: 'DAY' or 'GOOD_TILL_CANCEL'
    
    NOTE: Only available in demo accounts."""
)
async def place_stop_limit_order(ticker: str, quantity: float, stop_price: float, limit_price: float,
                                 time_validity: str) -> str:
    """Place a stop-limit order on 212 Trading API."""
    return await render_response(
        client.place_stop_limit_order(stop_price=stop_price, limit_price=limit_price, quantity=quantity, ticker=ticker, time_validity=Client212.TimeValidity(time_validity)))

@mcp.tool(
    title="Cancel order",
    description="Cancel an existing pending order by its ID. Returns confirmation once cancelled."
)
async def cancel_order(order_id: int) -> str:
    """Cancel an order on 212 Trading API."""
    await client.cancel_order(order_id)
    return f"Order with ID {order_id} cancelled."


@mcp.tool(
    title="Get order details",
    description="Retrieve detailed information about a specific order by its ID, including status, fill details, and timestamps."
)
async def get_order(order_id: int) -> str:
    """Get a specific order by ID from 212 Trading API."""
    return await render_response(client.get_order(order_id))


@mcp.tool(
    title="Search portfolio for position",
    description="""Search for a portfolio position by ticker symbol.
    
    IMPORTANT: Only searches current holdings. Will return 404 if you don't own this ticker.
    Same as get_portfolio_entry but with search-style endpoint."""
)
async def search_portfolio_entry(ticker: str) -> str:
    """Search for a portfolio entry by ticker from 212 Trading API."""
    return await render_response(client.search_portfolio_entry(ticker))


@mcp.tool(
    title="Create new pie",
    description="""Create a new investment pie with specified allocations.
    
    Parameters:
    - name: pie name
    - dividend_destination: 'CASH' or 'REINVEST'
    - instrument_shares: dict of {ticker: percentage} where percentages sum to 1.0
      Example: {'AAPL_US_EQ': 0.5, 'MSFT_US_EQ': 0.5} for 50/50 split
    - end_date: optional target completion date
    - goal: optional monetary goal for the pie
    
    Pies automatically maintain target allocations as you add funds."""
)
async def create_pie(name: str, dividend_destination: str, instrument_shares: dict[str, float],
                     end_date: datetime | None, goal: float | None) -> str:
    """Create a pie on 212 Trading API."""
    return await render_response(
        client.create_pie(name=name, dividend_destination=Client212.DividendDestination(dividend_destination),
                          instrument_shares=instrument_shares, end_date=end_date, goal=goal))


@mcp.tool(
    title="Update existing pie",
    description="""Update an existing pie's settings and allocations.
    
    Parameters same as create_pie. Changes take effect and portfolio will rebalance to match new allocations."""
)
async def update_pie(pie_id: int, name: str, dividend_destination: str, instrument_shares: dict[str, float],
                     end_date: datetime | None, goal: float | None) -> str:
    """Update a pie on 212 Trading API."""
    return await render_response(client.update_pie(pie_id=pie_id, name=name,
                                                   dividend_destination=Client212.DividendDestination(dividend_destination),
                                                   instrument_shares=instrument_shares, end_date=end_date, goal=goal))


@mcp.tool(
    title="Delete pie",
    description="Permanently delete a pie by its ID. Positions in the pie are NOT sold, just removed from pie management."
)
async def delete_pie(pie_id: int) -> str:
    """Delete a pie on 212 Trading API."""
    await client.delete_pie(pie_id)
    return f"Pie with ID {pie_id} deleted."


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
