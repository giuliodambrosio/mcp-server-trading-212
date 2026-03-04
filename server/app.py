from __future__ import annotations

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from server.account_config import build_clients_from_env
from server.prompts import register_prompts
from server.read_service import ReadService
from server.resources import register_resources
from server.tools import register_tools


def create_app() -> FastMCP:
    load_dotenv()

    clients, default_account = build_clients_from_env()

    mcp = FastMCP(
        "212-trading",
        instructions=(
            "Resource-first MCP server for Trading212. "
            "Use resources for read-only account data and tools for state-changing actions. "
            "All operations are account-scoped via trading212://accounts/{account}/... and account tool arguments. "
            "Supported account aliases are isa and invest. "
            "Call list_accounts first, then include account explicitly on every tool call and resource URI."
        ),
    )

    read_service = ReadService(clients, default_account)
    register_resources(mcp, read_service)
    register_tools(mcp, read_service)
    if hasattr(mcp, "prompt"):
        register_prompts(mcp)

    return mcp
