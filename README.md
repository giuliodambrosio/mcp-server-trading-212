# MCP Server for 212 Trading

A Model Context Protocol (MCP) server for Trading 212 with multi-account support.

## Setup

### Automated bootstrap (recommended)

Run:
```bash
./setup.sh
```

What `setup.sh` does:
- installs dependencies (`uv` when available, otherwise `pip`)
- configures multi-account `.env` interactively (`isa`, `invest`, or both)
- can update Claude Desktop MCP config (optional prompt)

### Manual setup (alternative)

1. Install dependencies:
   ```bash
   uv sync
   ```
2. Create local env file:
   ```bash
   cp .env.template .env
   ```
3. Edit `.env` with `isa`, `invest`, or both.
4. Run server:
   ```bash
   uv run python main.py
   ```

## Environment configuration

Supported account aliases are fixed to:
- `isa`
- `invest`

You can configure any combination of the two.

Both accounts:
```env
212_ACCOUNTS=isa,invest
212_DEFAULT_ACCOUNT=isa

212_ISA_API_KEY_ID=...
212_ISA_API_KEY_SECRET=...
212_ISA_API_BASE_LIVE_URL=https://live.trading212.com/api/v0/

212_INVEST_API_KEY_ID=...
212_INVEST_API_KEY_SECRET=...
212_INVEST_API_BASE_LIVE_URL=https://live.trading212.com/api/v0/
```

ISA only:
```env
212_ACCOUNTS=isa
212_DEFAULT_ACCOUNT=isa

212_ISA_API_KEY_ID=...
212_ISA_API_KEY_SECRET=...
212_ISA_API_BASE_LIVE_URL=https://live.trading212.com/api/v0/
```

Invest only:
```env
212_ACCOUNTS=invest
212_DEFAULT_ACCOUNT=invest

212_INVEST_API_KEY_ID=...
212_INVEST_API_KEY_SECRET=...
212_INVEST_API_BASE_LIVE_URL=https://live.trading212.com/api/v0/
```

## MCP resources

All resources are account-scoped:

- `trading212://accounts/{account}/info`
- `trading212://accounts/{account}/balance`
- `trading212://accounts/{account}/portfolio`
- `trading212://accounts/{account}/portfolio/{ticker}`
- `trading212://accounts/{account}/orders`
- `trading212://accounts/{account}/orders/{order_id}`
- `trading212://accounts/{account}/pies`
- `trading212://accounts/{account}/pies/{pie_id}`
- `trading212://accounts/{account}/dividends`
- `trading212://accounts/{account}/metadata/exchanges`
- `trading212://accounts/{account}/metadata/instruments/tickers`
- `trading212://accounts/{account}/metadata/instruments/{ticker}`

Use `{account}` as either `isa` or `invest`.

## MCP tools

Mutating tools require `account` (`isa` or `invest`):

- `place_market_order(account, ticker, quantity, extended_hours)`
- `place_limit_order(account, ticker, quantity, limit_price, time_validity)`
- `place_stop_order(account, ticker, quantity, stop_price, time_validity)`
- `place_stop_limit_order(account, ticker, quantity, stop_price, limit_price, time_validity)`
- `cancel_order(account, order_id)`
- `create_pie(account, name, dividend_destination, instrument_shares, end_date, goal)`
- `update_pie(account, pie_id, name, dividend_destination, instrument_shares, end_date, goal)`
- `delete_pie(account, pie_id)`

Other tools:
- `list_accounts()`
- `read_resource(uri)`
- `mcp_capabilities()`

`read_resource` compatibility aliases (also supported):
- `trading212://accounts/{account}/account/overview` -> account info
- `trading212://accounts/{account}/account/info` -> account info
- `trading212://accounts/{account}/account/balance` -> account balance

## Claude Desktop integration (optional)

This section is only for Claude Desktop users.  
If you use another MCP client, you can skip this and configure your client directly to run this server.

### Option A: let setup script update Claude config

```bash
./setup.sh --update-claude-config auto
```

This keeps your existing non-`212-trading` MCP entries and updates only `mcpServers["212-trading"]`.

### Option B: manual Claude config entry

Add this server to `mcpServers` in Claude Desktop config:

```json
{
  "command": "uv",
  "args": ["--directory", "/ABS/PATH/TO/mcp-server-212-trading", "run", "main.py"]
}
```

### Second account wiring in Claude

If Claude already runs this repo (`uv --directory <repo> run main.py`), only update `.env`:

```env
212_ACCOUNTS=isa,invest
212_DEFAULT_ACCOUNT=isa

212_INVEST_API_KEY_ID=<your invest account key id>
212_INVEST_API_KEY_SECRET=<your invest account key secret>
212_INVEST_API_BASE_LIVE_URL=https://live.trading212.com/api/v0/
```

Then restart Claude Desktop and use:
- `account=invest` for tools
- `trading212://accounts/invest/...` for resources

## Helping Claude use this correctly

When chatting with Claude, ask it to follow this sequence:
1. call `list_accounts()`
2. pick `isa` or `invest`
3. use only `trading212://accounts/{account}/...` resources
4. include `account` in every mutating tool call

Useful starter message:

```text
Before doing anything, call list_accounts(). Then use account=isa (or account=invest) explicitly in every tool call and trading212://accounts/{account}/... resource URI.
```

## Testing

```bash
uv run pytest
```
