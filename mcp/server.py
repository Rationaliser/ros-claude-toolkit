"""FastMCP entry point for ros-claude-toolkit.

Run directly: ``python mcp/server.py``. This file lives in ``mcp/`` which is a *script
directory*, not an importable package (there is intentionally no ``mcp/__init__.py``).
Running the script puts ``mcp/`` on ``sys.path[0]``, so ``import mcp`` inside FastMCP still
resolves to the installed MCP SDK, while our own modules import as siblings.
"""

import logging

from fastmcp import FastMCP

from rosbridge_client import RosbridgeClient
from tools.params import register_param_tools
from tools.services import register_service_tools
from tools.topics import register_topic_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

mcp = FastMCP("ros-claude-toolkit")
client = RosbridgeClient()

register_topic_tools(mcp, client)
register_service_tools(mcp, client)
register_param_tools(mcp, client)


if __name__ == "__main__":
    logger.info("Starting ros-claude-toolkit MCP server")
    mcp.run()
