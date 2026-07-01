"""Parameter tools: ros_get_param, ros_set_param.

Params carry no safety constraints, but every call is still audit-logged via ``log_and_return``
so the command log is a complete record of Claude-issued tool calls.
"""

import logging
from typing import Any

from fastmcp import FastMCP

from rosbridge_client import RosbridgeClient
from safety.logger import log_and_return

logger = logging.getLogger(__name__)


def register_param_tools(mcp: FastMCP, client: RosbridgeClient) -> None:
    """Register parameter-related MCP tools on the given FastMCP server."""

    @mcp.tool()
    def ros_get_param(name: str) -> dict:
        """Read the value of a ROS parameter."""
        if not name or not name.strip():
            return log_and_return("ros_get_param", {"name": name}, {
                "status": "error",
                "data": None,
                "message": "Parameter name cannot be empty.",
                "safety_applied": False,
            })
        value = client.get_param(name)
        logger.info("ros_get_param: %s", name)
        return log_and_return("ros_get_param", {"name": name}, {
            "status": "success",
            "data": {"name": name, "value": value},
            "message": f"Read parameter {name}.",
            "safety_applied": False,
        })

    @mcp.tool()
    def ros_set_param(name: str, value: Any) -> dict:
        """Set the value of a ROS parameter."""
        args = {"name": name, "value": value}
        if not name or not name.strip():
            return log_and_return("ros_set_param", args, {
                "status": "error",
                "data": None,
                "message": "Parameter name cannot be empty.",
                "safety_applied": False,
            })
        client.set_param(name, value)
        logger.info("ros_set_param: %s = %r", name, value)
        return log_and_return("ros_set_param", args, {
            "status": "success",
            "data": {"name": name, "value": value},
            "message": f"Set parameter {name}.",
            "safety_applied": False,
        })
