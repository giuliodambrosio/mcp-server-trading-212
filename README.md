# MCP Server for 212 Trading

A Model Context Protocol (MCP) server for accessing a single 212 Trading account.

## What changed

This server now follows a resource-first MCP structure:
- Use **resources** for read-only data.
- Use **tools** for state-changing operations.
- Legacy read tools are still available for compatibility, but deprecated.

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Configure environment:
   ```bash
   cp .env.template .env
   ```

   Fill in:
   ```env
   212_API_KEY_ID=your_api_key_id
   212_API_KEY_SECRET=your_api_secret
   212_API_BASE_LIVE_URL=https://live.trading212.com/api/v0
   ```

3. Run server:
   ```bash
   python main.py
   ```

## MCP Resources (primary read interface)

- `trading212://account/info`
- `trading212://account/balance`
- `trading212://portfolio`
- `trading212://portfolio/{ticker}`
- `trading212://orders`
- `trading212://orders/{order_id}`
- `trading212://pies`
- `trading212://pies/{pie_id}`
- `trading212://dividends`
- `trading212://metadata/exchanges`
- `trading212://metadata/instruments/tickers`
- `trading212://metadata/instruments/{ticker}`

Each resource returns JSON with:
- `data`
- `generated_at`
- `source_endpoint`
- `warnings` (optional)

## MCP Tools (mutating)

- `place_market_order(ticker, quantity, extended_hours)`
- `place_limit_order(ticker, quantity, limit_price, time_validity)`
- `place_stop_order(ticker, quantity, stop_price, time_validity)`
- `place_stop_limit_order(ticker, quantity, stop_price, limit_price, time_validity)`
- `cancel_order(order_id)`
- `create_pie(name, dividend_destination, instrument_shares, end_date, goal)`
- `update_pie(pie_id, name, dividend_destination, instrument_shares, end_date, goal)`
- `delete_pie(pie_id)`

Compatibility helper for clients without native MCP resource reads:
- `read_resource(uri)` - reads any supported `trading212://...` URI and returns the same resource payload envelope.
- `mcp_capabilities()` - diagnostic output listing registered tools/resources/resource templates.

Dividend destination accepts `REINVEST` and `CASH` (`CASH` is normalized internally to `TO_ACCOUNT_CASH`).

## Deprecated compatibility tools (read-only)

Still available:
- `get_account_info`, `get_balance`, `get_portfolio`, `get_portfolio_entry`
- `get_instruments`, `get_instrument_tickers`, `get_exchanges`, `get_paid_dividends`
- `get_pies`, `get_pie`, `get_orders`, `get_order`

These wrappers are deprecated in favor of resources.

## Testing

Run tests:

```bash
pytest
```

Coverage (optional):

```bash
pytest --cov=server --cov-report=term-missing
```

## Notes

- `search_portfolio_entry` is intentionally not part of the public MCP surface.
- The client includes retry handling for HTTP 429 and non-blocking rate-limit waits.
- `main.py` is now bootstrap-only; MCP registration lives in `server/` modules.
