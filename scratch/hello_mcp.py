"""Throwaway hello-world MCP server for Week 1 fastmcp verification."""

import logging
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("ros-claude-hello")


@mcp.tool()
def ping() -> dict:
    """Return a pong response to confirm the MCP server is reachable."""
    logger.info("ping called")
    return {"status": "success", "data": "pong", "message": "MCP server is reachable.", "safety_applied": False}


if __name__ == "__main__":
    mcp.run()
