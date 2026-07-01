"""Topic tools: ros_list_topics, ros_echo_topic, ros_publish_topic.

Every ``/cmd_vel`` publish is routed through ``SafetyMiddleware().apply(topic, message)`` — the
velocity clamp and workspace-bounds check that are the project's safety guarantee (see
.claude/rules/safety-layer.md). The middleware is instantiated per publish so live edits to
safety_config.yaml take effect immediately. Every tool call is audit-logged via ``log_and_return``.
"""

import logging

from fastmcp import FastMCP

from rosbridge_client import RosbridgeClient
from safety.logger import log_and_return
from safety.middleware import SafetyMiddleware

logger = logging.getLogger(__name__)

# Sensible default so "move the robot" works without the caller knowing ROS message types.
_CMD_VEL_DEFAULT_TYPE = "geometry_msgs/Twist"


def _resolve_msg_type(client: RosbridgeClient, topic: str, msg_type: str | None) -> str:
    """Return an explicit msg_type, else look it up, else fall back for /cmd_vel."""
    if msg_type:
        return msg_type
    resolved = client.topic_type(topic)
    if resolved:
        return resolved
    if topic.rstrip("/").endswith("cmd_vel"):
        return _CMD_VEL_DEFAULT_TYPE
    return ""


def register_topic_tools(mcp: FastMCP, client: RosbridgeClient) -> None:
    """Register topic-related MCP tools on the given FastMCP server."""

    @mcp.tool()
    def ros_list_topics() -> dict:
        """List all active ROS topics with their message types."""
        result = client.list_topics()
        topics = result.get("topics", [])
        types = result.get("types", [])
        logger.info("ros_list_topics: %d topics", len(topics))
        return log_and_return("ros_list_topics", {}, {
            "status": "success",
            "data": {"topics": topics, "types": types, "count": len(topics)},
            "message": f"Found {len(topics)} active topics.",
            "safety_applied": False,
        })

    @mcp.tool()
    def ros_echo_topic(
        topic: str, count: int = 1, msg_type: str | None = None, timeout: float = 5.0
    ) -> dict:
        """Return up to the last `count` messages received on a topic."""
        args = {"topic": topic, "count": count, "msg_type": msg_type}
        if not topic or not topic.strip():
            return log_and_return("ros_echo_topic", args, {
                "status": "error",
                "data": None,
                "message": "Topic name cannot be empty.",
                "safety_applied": False,
            })
        resolved_type = _resolve_msg_type(client, topic, msg_type)
        if not resolved_type:
            return log_and_return("ros_echo_topic", args, {
                "status": "error",
                "data": None,
                "message": f"Could not resolve message type for {topic}; pass msg_type explicitly.",
                "safety_applied": False,
            })
        messages = client.echo_topic(topic, resolved_type, count=count, timeout=timeout)
        logger.info("ros_echo_topic: %s -> %d message(s)", topic, len(messages))
        return log_and_return("ros_echo_topic", args, {
            "status": "success",
            "data": {"topic": topic, "type": resolved_type, "messages": messages},
            "message": f"Received {len(messages)} message(s) from {topic}.",
            "safety_applied": False,
        })

    @mcp.tool()
    def ros_publish_topic(topic: str, message: dict, msg_type: str | None = None) -> dict:
        """Publish a message to a topic; cmd_vel publishes route through the safety layer."""
        args = {"topic": topic, "message": message, "msg_type": msg_type}
        if not topic or not topic.strip():
            return log_and_return("ros_publish_topic", args, {
                "status": "error",
                "data": None,
                "message": "Topic name cannot be empty.",
                "safety_applied": False,
            })
        resolved_type = _resolve_msg_type(client, topic, msg_type)
        if not resolved_type:
            return log_and_return("ros_publish_topic", args, {
                "status": "error",
                "data": None,
                "message": f"Could not resolve message type for {topic}; pass msg_type explicitly.",
                "safety_applied": False,
            })

        # Safety layer: velocity clamp for /cmd_vel, workspace bounds for position topics.
        safe_message, event = SafetyMiddleware().apply(topic, message)
        if event.outcome == "blocked":
            logger.warning("ros_publish_topic blocked: %s", event.reason)
            return log_and_return("ros_publish_topic", args, {
                "status": "blocked",
                "data": None,
                "message": event.reason,
                "safety_applied": event.applied,
            })

        client.publish_topic(topic, resolved_type, safe_message)
        logger.info("ros_publish_topic: %s (%s) outcome=%s", topic, resolved_type, event.outcome)
        return log_and_return("ros_publish_topic", args, {
            "status": event.outcome,
            "data": {"topic": topic, "type": resolved_type, "message": safe_message},
            "message": event.reason,
            "safety_applied": event.applied,
        })
