"""Shared test fixtures.

Mirrors the server's import model: ``mcp/`` is put on sys.path so tool modules import as
siblings (``from rosbridge_client import ...``), exactly as ``python mcp/server.py`` does.
Tool tests run against a FakeClient, so no live rosbridge/Gazebo is required.
"""

import asyncio
import os
import sys

import pytest

MCP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp")
if MCP_DIR not in sys.path:
    sys.path.insert(0, MCP_DIR)

from fastmcp import FastMCP  # noqa: E402  (import after sys.path setup)

from tools.params import register_param_tools  # noqa: E402
from tools.services import register_service_tools  # noqa: E402
from tools.topics import register_topic_tools  # noqa: E402


class FakeClient:
    """In-memory stand-in for RosbridgeClient with canned data and recorded writes."""

    def __init__(self) -> None:
        self.is_connected = True
        self.published: list[tuple[str, str, dict]] = []
        self.params: dict[str, object] = {"/use_sim_time": True}

    # topics
    def list_topics(self) -> dict:
        return {
            "topics": ["/cmd_vel", "/odom", "/scan"],
            "types": ["geometry_msgs/Twist", "nav_msgs/Odometry", "sensor_msgs/LaserScan"],
        }

    def topic_type(self, topic: str) -> str:
        return {"/cmd_vel": "geometry_msgs/Twist", "/odom": "nav_msgs/Odometry"}.get(topic, "")

    def echo_topic(self, topic, msg_type, count=1, timeout=None) -> list:
        return [{"linear": {"x": 0.1}, "angular": {"z": 0.0}}][:count]

    def publish_topic(self, topic, msg_type, message) -> None:
        self.published.append((topic, msg_type, message))

    # services
    def list_services(self) -> dict:
        return {"services": ["/reset_simulation", "/rosapi/topics"]}

    def service_type(self, service: str) -> str:
        return {"/reset_simulation": "std_srvs/Empty"}.get(service, "")

    def call_service(self, service, srv_type, args=None) -> dict:
        return {"called": service, "args": args or {}}

    # params
    def get_param(self, name: str):
        return self.params.get(name)

    def set_param(self, name: str, value) -> None:
        self.params[name] = value


def _build_tool_map(client) -> dict:
    """Register all tools against a client and return {tool_name: callable fn}."""
    mcp = FastMCP("test")
    register_topic_tools(mcp, client)
    register_service_tools(mcp, client)
    register_param_tools(mcp, client)
    names = [
        "ros_list_topics",
        "ros_echo_topic",
        "ros_publish_topic",
        "ros_list_services",
        "ros_call_service",
        "ros_get_param",
        "ros_set_param",
    ]
    return {name: asyncio.run(mcp.get_tool(name)).fn for name in names}


@pytest.fixture
def fake_client() -> FakeClient:
    """A fresh FakeClient per test."""
    return FakeClient()


@pytest.fixture
def tools(fake_client) -> dict:
    """Mapping of tool name -> registered tool function, wired to the fake client."""
    return _build_tool_map(fake_client)
