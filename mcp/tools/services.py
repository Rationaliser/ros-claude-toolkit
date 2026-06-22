"""Service tools: ros_list_services, ros_call_service.

The confirmation gate for blacklisted services is Week 3 work (.claude/rules/safety-layer.md).
A ``confirm`` kwarg will be added to ros_call_service then; it is intentionally absent now.
"""

import logging

from fastmcp import FastMCP

from rosbridge_client import RosbridgeClient

logger = logging.getLogger(__name__)


def register_service_tools(mcp: FastMCP, client: RosbridgeClient) -> None:
    """Register service-related MCP tools on the given FastMCP server."""

    @mcp.tool()
    def ros_list_services() -> dict:
        """List all available ROS services."""
        result = client.list_services()
        services = result.get("services", [])
        logger.info("ros_list_services: %d services", len(services))
        return {
            "status": "success",
            "data": {"services": services, "count": len(services)},
            "message": f"Found {len(services)} available services.",
            "safety_applied": False,
        }

    @mcp.tool()
    def ros_call_service(
        service: str, args: dict | None = None, srv_type: str | None = None
    ) -> dict:
        """Call a ROS service with optional arguments, resolving the type when omitted."""
        if not service or not service.strip():
            return {
                "status": "error",
                "data": None,
                "message": "Service name cannot be empty.",
                "safety_applied": False,
            }
        resolved_type = srv_type or client.service_type(service)
        if not resolved_type:
            return {
                "status": "error",
                "data": None,
                "message": f"Could not resolve service type for {service}; pass srv_type explicitly.",
                "safety_applied": False,
            }
        response = client.call_service(service, resolved_type, args or {})
        logger.info("ros_call_service: %s (%s)", service, resolved_type)
        return {
            "status": "success",
            "data": {"service": service, "type": resolved_type, "response": response},
            "message": f"Called {service}.",
            "safety_applied": False,
        }
