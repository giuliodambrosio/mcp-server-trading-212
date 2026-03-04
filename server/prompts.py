from __future__ import annotations

from typing import Any


def register_prompts(mcp: Any) -> None:
    @mcp.prompt(title="Account selection prompt")
    def account_selection_prompt() -> str:
        return (
            "First call list_accounts() to discover configured accounts. "
            "Then include account explicitly on all tool calls and resources, "
            "for example trading212://accounts/isa/info or trading212://accounts/invest/portfolio."
        )

    @mcp.prompt(title="Portfolio analysis prompt")
    def portfolio_analysis_prompt() -> str:
        return (
            "First call list_accounts() and choose one account alias. "
            "Use resources in this order: trading212://accounts/{account}/info, trading212://accounts/{account}/balance, "
            "trading212://accounts/{account}/portfolio, trading212://accounts/{account}/metadata/instruments/tickers "
            "or trading212://accounts/{account}/metadata/instruments/{ticker}. "
            "Respect instrument currency units (e.g. GBX in pence) and do not assume all prices are in account currency."
        )
