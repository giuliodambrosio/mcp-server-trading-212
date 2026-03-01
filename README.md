# MCP Server for 212 Trading

A Model Context Protocol (MCP) server for accessing a single 212 Trading account.

## Setup

1. Run interactive setup script (recommended):
   ```bash
   ./setup.sh
   ```
   The script can:
   - install dependencies (`uv` if available, otherwise `pip`)
   - guide you through `.env` credential setup
   - show current `.env` (redacted) before overwrite and ask for confirmation
   - update Claude Desktop config idempotently (`mcpServers["212-trading"]`)

2. Optional setup flags:
   ```bash
   # auto-update Claude config without prompts
   ./setup.sh --update-claude-config auto

   # test config updates safely in a sandbox directory
   ./setup.sh --claude-config-dir /tmp/claude-test --update-claude-config auto --non-interactive --skip-install --skip-validation
   ```

3. Manual fallback only (if you do not use `setup.sh`):
   ```bash
   uv sync
   cp .env.template .env
   # edit .env and set:
   # 212_API_KEY_ID
   # 212_API_KEY_SECRET
   # 212_API_BASE_LIVE_URL
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
