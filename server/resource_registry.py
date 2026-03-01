from __future__ import annotations

# Concrete resources
ACCOUNT_INFO = "trading212://account/info"
ACCOUNT_BALANCE = "trading212://account/balance"
PORTFOLIO = "trading212://portfolio"
ORDERS = "trading212://orders"
PIES = "trading212://pies"
DIVIDENDS = "trading212://dividends"
EXCHANGES = "trading212://metadata/exchanges"
INSTRUMENT_TICKERS = "trading212://metadata/instruments/tickers"

# Template resources
PORTFOLIO_TICKER = "trading212://portfolio/{ticker}"
ORDER_ID = "trading212://orders/{order_id}"
PIE_ID = "trading212://pies/{pie_id}"
INSTRUMENT_TICKER = "trading212://metadata/instruments/{ticker}"

CONCRETE_RESOURCE_URIS: tuple[str, ...] = (
    ACCOUNT_INFO,
    ACCOUNT_BALANCE,
    PORTFOLIO,
    ORDERS,
    PIES,
    DIVIDENDS,
    EXCHANGES,
    INSTRUMENT_TICKERS,
)

TEMPLATE_RESOURCE_URIS: tuple[str, ...] = (
    PORTFOLIO_TICKER,
    ORDER_ID,
    PIE_ID,
    INSTRUMENT_TICKER,
)
