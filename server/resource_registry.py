from __future__ import annotations

ACCOUNT_INFO = "trading212://accounts/{account}/info"
ACCOUNT_BALANCE = "trading212://accounts/{account}/balance"
PORTFOLIO = "trading212://accounts/{account}/portfolio"
ORDERS = "trading212://accounts/{account}/orders"
PIES = "trading212://accounts/{account}/pies"
DIVIDENDS = "trading212://accounts/{account}/dividends"
EXCHANGES = "trading212://accounts/{account}/metadata/exchanges"
INSTRUMENT_TICKERS = "trading212://accounts/{account}/metadata/instruments/tickers"
PORTFOLIO_TICKER = "trading212://accounts/{account}/portfolio/{ticker}"
ORDER_ID = "trading212://accounts/{account}/orders/{order_id}"
PIE_ID = "trading212://accounts/{account}/pies/{pie_id}"
INSTRUMENT_TICKER = "trading212://accounts/{account}/metadata/instruments/{ticker}"

RESOURCE_URIS: tuple[str, ...] = (
    ACCOUNT_INFO,
    ACCOUNT_BALANCE,
    PORTFOLIO,
    PORTFOLIO_TICKER,
    ORDERS,
    ORDER_ID,
    PIES,
    PIE_ID,
    DIVIDENDS,
    EXCHANGES,
    INSTRUMENT_TICKERS,
    INSTRUMENT_TICKER,
)
