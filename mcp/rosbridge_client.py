"""roslibpy WebSocket wrapper for the ros-claude-toolkit MCP server.

Thin transport layer over rosbridge (ADR-002). One persistent ``roslibpy.Ros`` connection is
created lazily on first use and reused; roslibpy runs its own background event-loop thread, so
this avoids the asyncio/rclpy spin conflict that motivated the rosbridge choice.

This module is pure transport: it returns raw roslibpy/rosapi results and raises on failure.
Shaping results into the ``{status, data, message, safety_applied}`` tool contract is the job of
the ``mcp/tools/*`` modules, not this one.

rosapi service names and the advertise/subscribe/publish message flow follow the rosbridge
protocol; the protocol shape was cross-checked against robotmcp/ros-mcp-server (Apache-2.0), but
this implementation uses roslibpy's high-level Topic/Service/Param wrappers rather than raw
websocket frames.
"""

import json
import logging
import threading
import time
from typing import Any

import roslibpy

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9090
DEFAULT_TIMEOUT = 5.0

_ROSBRIDGE_HINT = (
    "rosbridge WebSocket not reachable at {host}:{port}. Start it with: "
    "ros2 launch rosbridge_server rosbridge_websocket_launch.xml"
)


class RosbridgeClient:
    """Persistent roslibpy connection to a rosbridge server, with lazy connect/reconnect."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Configure (but do not yet open) a rosbridge connection."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self._ros: roslibpy.Ros | None = None
        self._lock = threading.RLock()

    @property
    def is_connected(self) -> bool:
        """Return True if the underlying rosbridge connection is currently open."""
        return self._ros is not None and self._ros.is_connected

    def connect(self) -> None:
        """Open the rosbridge connection, raising ConnectionError if it cannot be established."""
        with self._lock:
            if self.is_connected:
                return
            self._ros = roslibpy.Ros(host=self.host, port=self.port)
            try:
                self._ros.run(timeout=self.timeout)
            except Exception as exc:  # roslibpy raises on connect timeout/failure
                self._ros = None
                raise ConnectionError(
                    _ROSBRIDGE_HINT.format(host=self.host, port=self.port)
                ) from exc
            if not self._ros.is_connected:
                self._ros = None
                raise ConnectionError(_ROSBRIDGE_HINT.format(host=self.host, port=self.port))
            logger.info("Connected to rosbridge at %s:%s", self.host, self.port)

    def close(self) -> None:
        """Close the rosbridge connection if open."""
        with self._lock:
            if self._ros is not None:
                try:
                    self._ros.close()
                finally:
                    self._ros = None
                    logger.info("Closed rosbridge connection")

    def _ensure_connected(self) -> roslibpy.Ros:
        """Return a live roslibpy.Ros, connecting first if needed."""
        self.connect()
        assert self._ros is not None  # connect() raises if it cannot establish a connection
        return self._ros

    def _call_rosapi(self, service: str, srv_type: str, args: dict | None = None) -> dict:
        """Call a rosapi service and return its result dict."""
        ros = self._ensure_connected()
        client = roslibpy.Service(ros, service, srv_type)
        request = roslibpy.ServiceRequest(args or {})
        return client.call(request, timeout=self.timeout)

    # --- topics -----------------------------------------------------------------

    def list_topics(self) -> dict:
        """Return rosapi /topics result: {'topics': [...], 'types': [...]}."""
        return self._call_rosapi("/rosapi/topics", "rosapi/Topics")

    def topic_type(self, topic: str) -> str:
        """Return the message type advertised for a topic, or '' if unknown."""
        result = self._call_rosapi("/rosapi/topic_type", "rosapi/TopicType", {"topic": topic})
        return result.get("type", "")

    def echo_topic(
        self, topic: str, msg_type: str, count: int = 1, timeout: float | None = None
    ) -> list[dict]:
        """Subscribe to a topic and return up to ``count`` messages, then unsubscribe."""
        ros = self._ensure_connected()
        deadline = time.time() + (timeout if timeout is not None else self.timeout)
        received: list[dict] = []
        done = threading.Event()
        listener = roslibpy.Topic(ros, topic, msg_type)

        def _on_message(message: dict) -> None:
            if len(received) < count:
                received.append(message)
            if len(received) >= count:
                done.set()

        listener.subscribe(_on_message)
        try:
            while not done.is_set() and time.time() < deadline:
                done.wait(timeout=0.1)
        finally:
            listener.unsubscribe()
        return received

    def publish_topic(self, topic: str, msg_type: str, message: dict) -> None:
        """Advertise (if needed) and publish a single message to a topic."""
        ros = self._ensure_connected()
        publisher = roslibpy.Topic(ros, topic, msg_type)
        publisher.publish(roslibpy.Message(message))
        publisher.unadvertise()

    # --- services ---------------------------------------------------------------

    def list_services(self) -> dict:
        """Return rosapi /services result: {'services': [...]}."""
        return self._call_rosapi("/rosapi/services", "rosapi/Services")

    def service_type(self, service: str) -> str:
        """Return the service type for a service name, or '' if unknown."""
        result = self._call_rosapi(
            "/rosapi/service_type", "rosapi/ServiceType", {"service": service}
        )
        return result.get("type", "")

    def call_service(self, service: str, srv_type: str, args: dict | None = None) -> dict:
        """Call an arbitrary ROS service and return its response dict."""
        ros = self._ensure_connected()
        client = roslibpy.Service(ros, service, srv_type)
        request = roslibpy.ServiceRequest(args or {})
        return client.call(request, timeout=self.timeout)

    # --- parameters -------------------------------------------------------------

    def get_param(self, name: str) -> Any:
        """Read a ROS parameter via rosapi; returns None if unset.

        Uses the rosapi GetParam service directly (rather than roslibpy.Param, which raises on
        an empty/unset value) so an unset parameter is reported cleanly instead of crashing.
        """
        result = self._call_rosapi("/rosapi/get_param", "rosapi/GetParam", {"name": name})
        raw = result.get("value", "")
        if raw == "":
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    def set_param(self, name: str, value: Any) -> None:
        """Write a ROS parameter value via the rosapi SetParam service."""
        self._call_rosapi(
            "/rosapi/set_param", "rosapi/SetParam", {"name": name, "value": json.dumps(value)}
        )
