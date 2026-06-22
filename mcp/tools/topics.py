"""Topic tools: ros_list_topics, ros_echo_topic, ros_publish_topic.

ros_publish_topic routes every publish through ``_apply_safety`` so that in Week 3 the real
``SafetyMiddleware().apply(topic, message)`` slots in at the same call site with no refactor
(see .claude/rules/safety-layer.md). For Week 2 ``_apply_safety`` is a deliberate no-op
pass-through — no clamping, no bounds, no gate. The wrapper *shape* is what matters now.
"""

import logging
from dataclasses import dataclass

from fastmcp import FastMCP

from rosbridge_client import RosbridgeClient

logger = logging.getLogger(__name__)

# Sensible default so "move the robot" works without the caller knowing ROS message types.
_CMD_VEL_DEFAULT_TYPE = "geometry_msgs/Twist"


@dataclass
class SafetyEvent:
    """Outcome of a safety check on an outbound publish."""

    outcome: str  # one of: success | clamped | blocked | error
    reason: str
    applied: bool


def _apply_safety(topic: str, message: dict) -> tuple[dict, SafetyEvent]:
    """Week 2 no-op safety hook; Week 3 replaces the body with SafetyMiddleware().apply()."""
    return message, SafetyEvent(
        outcome="success",
        reason=f"Published to {topic} (no safety constraints enforced yet — Week 3).",
        applied=False,
    )


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
        return {
            "status": "success",
            "data": {"topics": topics, "types": types, "count": len(topics)},
            "message": f"Found {len(topics)} active topics.",
            "safety_applied": False,
        }

    @mcp.tool()
    def ros_echo_topic(
        topic: str, count: int = 1, msg_type: str | None = None, timeout: float = 5.0
    ) -> dict:
        """Return up to the last `count` messages received on a topic."""
        if not topic or not topic.strip():
            return {
                "status": "error",
                "data": None,
                "message": "Topic name cannot be empty.",
                "safety_applied": False,
            }
        resolved_type = _resolve_msg_type(client, topic, msg_type)
        if not resolved_type:
            return {
                "status": "error",
                "data": None,
                "message": f"Could not resolve message type for {topic}; pass msg_type explicitly.",
                "safety_applied": False,
            }
        messages = client.echo_topic(topic, resolved_type, count=count, timeout=timeout)
        logger.info("ros_echo_topic: %s -> %d message(s)", topic, len(messages))
        return {
            "status": "success",
            "data": {"topic": topic, "type": resolved_type, "messages": messages},
            "message": f"Received {len(messages)} message(s) from {topic}.",
            "safety_applied": False,
        }

    @mcp.tool()
    def ros_publish_topic(topic: str, message: dict, msg_type: str | None = None) -> dict:
        """Publish a message to a topic; cmd_vel publishes route through the safety hook."""
        if not topic or not topic.strip():
            return {
                "status": "error",
                "data": None,
                "message": "Topic name cannot be empty.",
                "safety_applied": False,
            }
        resolved_type = _resolve_msg_type(client, topic, msg_type)
        if not resolved_type:
            return {
                "status": "error",
                "data": None,
                "message": f"Could not resolve message type for {topic}; pass msg_type explicitly.",
                "safety_applied": False,
            }

        # Week 3: SafetyMiddleware().apply(topic, message) slots in here unchanged.
        safe_message, event = _apply_safety(topic, message)
        if event.outcome == "blocked":
            logger.warning("ros_publish_topic blocked: %s", event.reason)
            return {
                "status": "blocked",
                "data": None,
                "message": event.reason,
                "safety_applied": event.applied,
            }

        client.publish_topic(topic, resolved_type, safe_message)
        logger.info("ros_publish_topic: %s (%s) outcome=%s", topic, resolved_type, event.outcome)
        return {
            "status": event.outcome,
            "data": {"topic": topic, "type": resolved_type, "message": safe_message},
            "message": event.reason,
            "safety_applied": event.applied,
        }
