"""Service tools: ros_list_services, ros_call_service.

Services listed under ``confirmation_required`` in safety_config.yaml (e.g. emergency stop) are
guarded by ``ConfirmationGate``: a call without ``confirm=True`` is blocked, never executed.
``confirm=True`` is the single, audit-logged bypass. Every tool call is logged via
``log_and_return`` (see .claude/rules/safety-layer.md).
"""

import logging

from fastmcp import FastMCP

from rosbridge_client import RosbridgeClient
from safety.gate import ConfirmationGate, ConfirmationRequired
from safety.logger import log_and_return

logger = logging.getLogger(__name__)


def register_service_tools(mcp: FastMCP, client: RosbridgeClient) -> None:
    """Register service-related MCP tools on the given FastMCP server."""

    @mcp.tool()
    def ros_list_services() -> dict:
        """List all available ROS services."""
        result = client.list_services()
        services = result.get("services", [])
        logger.info("ros_list_services: %d services", len(services))
        return log_and_return("ros_list_services", {}, {
            "status": "success",
            "data": {"services": services, "count": len(services)},
            "message": f"Found {len(services)} available services.",
            "safety_applied": False,
        })

    @mcp.tool()
    def ros_call_service(
        service: str,
        args: dict | None = None,
        srv_type: str | None = None,
        confirm: bool = False,
    ) -> dict:
        """Call a ROS service; confirmation-required services need confirm=True to proceed."""
        log_args = {"service": service, "args": args, "srv_type": srv_type, "confirm": confirm}
        if not service or not service.strip():
            return log_and_return("ros_call_service", log_args, {
                "status": "error",
                "data": None,
                "message": "Service name cannot be empty.",
                "safety_applied": False,
            })
        gate = ConfirmationGate()
        is_gated = service in gate.required
        if not confirm:
            try:
                gate.check(service)
            except ConfirmationRequired as exc:
                logger.warning("ros_call_service gated: %s", service)
                return log_and_return("ros_call_service", log_args, {
                    "status": "blocked",
                    "data": None,
                    "message": str(exc),
                    "safety_applied": True,
                })
        resolved_type = srv_type or client.service_type(service)
        if not resolved_type:
            return log_and_return("ros_call_service", log_args, {
                "status": "error",
                "data": None,
                "message": f"Could not resolve service type for {service}; pass srv_type explicitly.",
                "safety_applied": False,
            })
        response = client.call_service(service, resolved_type, args or {})
        logger.info("ros_call_service: %s (%s) confirm=%s", service, resolved_type, confirm)
        return log_and_return("ros_call_service", log_args, {
            "status": "success",
            "data": {"service": service, "type": resolved_type, "response": response},
            "message": f"Called {service}.",
            "safety_applied": is_gated,
        })
