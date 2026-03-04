from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from server.prompts import register_prompts


@dataclass
class PromptRegistration:
    name: str
    meta: dict[str, Any]
    fn: Callable[..., Any]


class FakePromptMCP:
    def __init__(self) -> None:
        self.prompts: list[PromptRegistration] = []

    def prompt(self, **kwargs: Any):
        def decorator(fn: Callable[..., Any]):
            self.prompts.append(PromptRegistration(name=fn.__name__, meta=kwargs, fn=fn))
            return fn

        return decorator


def test_register_prompts_exposes_account_and_portfolio_prompts():
    mcp = FakePromptMCP()
    register_prompts(mcp)

    prompt_entries = {entry.name: entry for entry in mcp.prompts}

    account_prompt = prompt_entries["account_selection_prompt"].fn()
    portfolio_prompt = prompt_entries["portfolio_analysis_prompt"].fn()

    assert "list_accounts()" in account_prompt
    assert "trading212://accounts/isa/info" in account_prompt
    assert "trading212://accounts/{account}/portfolio" in portfolio_prompt
    assert "Respect instrument currency units" in portfolio_prompt
