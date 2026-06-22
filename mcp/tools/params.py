"""Parameter tools: ros_get_param, ros_set_param."""

import logging
from typing import Any

from fastmcp import FastMCP

from rosbridge_client import RosbridgeClient

logger = logging.getLogger(__name__)


def register_param_tools(mcp: FastMCP, client: RosbridgeClient) -> None:
    """Register parameter-related MCP tools on the given FastMCP server."""

    @mcp.tool()
    def ros_get_param(name: str) -> dict:
        """Read the value of a ROS parameter."""
        if not name or not name.strip():
            return {
                "status": "error",
                "data": None,
                "message": "Parameter name cannot be empty.",
                "safety_applied": False,
            }
        value = client.get_param(name)
        logger.info("ros_get_param: %s", name)
        return {
            "status": "success",
            "data": {"name": name, "value": value},
            "message": f"Read parameter {name}.",
            "safety_applied": False,
        }

    @mcp.tool()
    def ros_set_param(name: str, value: Any) -> dict:
        """Set the value of a ROS parameter."""
        if not name or not name.strip():
            return {
                "status": "error",
                "data": None,
                "message": "Parameter name cannot be empty.",
                "safety_applied": False,
            }
        client.set_param(name, value)
        logger.info("ros_set_param: %s = %r", name, value)
        return {
            "status": "success",
            "data": {"name": name, "value": value},
            "message": f"Set parameter {name}.",
            "safety_applied": False,
        }
