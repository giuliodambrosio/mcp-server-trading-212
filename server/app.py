from __future__ import annotations

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from server.client212 import Client212
from server.prompts import register_prompts
from server.read_service import ReadService
from server.resources import register_resources
from server.tools import register_tools


def create_app() -> FastMCP:
    load_dotenv()

    client = Client212(
        os.getenv("212_API_KEY_ID", ""),
        os.getenv("212_API_KEY_SECRET", ""),
        os.getenv("212_API_BASE_LIVE_URL", ""),
    )

    mcp = FastMCP(
        "212-trading",
        instructions=(
            "Resource-first MCP server for Trading212. "
            "Use resources for read-only account data and tools for state-changing actions."
        ),
    )

    read_service = ReadService(client)
    register_resources(mcp, read_service)
    register_tools(mcp, client, read_service)
    if hasattr(mcp, "prompt"):
        register_prompts(mcp)

    return mcp
