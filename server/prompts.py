from __future__ import annotations

from typing import Any


def register_prompts(mcp: Any) -> None:
    @mcp.prompt(title="Portfolio analysis prompt")
    def portfolio_analysis_prompt() -> str:
        return (
            "Use resources in this order: trading212://account/info, trading212://account/balance, "
            "trading212://portfolio, trading212://metadata/instruments/tickers or trading212://metadata/instruments/{ticker}. "
            "Respect instrument currency units (e.g. GBX in pence) and do not assume all prices are in account currency."
        )
