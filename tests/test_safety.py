"""Safety-layer tests: velocity clamping, workspace bounds, confirmation gate, command log.

Unit tests drive the safety classes directly with an injected temp config (``safety_config_path``
fixture). Tool-level tests go through the registered MCP tools (``tools`` fixture), which read the
same temp config via the ``ROS_SAFETY_CONFIG`` env override set autouse in conftest. No live ROS.
"""

import json

import pytest

from safety.gate import ConfirmationGate, ConfirmationRequired
from safety.logger import CommandLogger
from safety.middleware import SafetyMiddleware

CONTRACT_KEYS = {"status", "data", "message", "safety_applied"}


def _assert_contract(result: dict) -> None:
    assert CONTRACT_KEYS.issubset(result.keys())
    assert isinstance(result["safety_applied"], bool)


# --- SafetyMiddleware: velocity clamping ------------------------------------

def test_middleware_clamps_linear_x_over_limit(safety_config_path):
    mw = SafetyMiddleware(config_path=safety_config_path)
    safe, event = mw.apply("/cmd_vel", {"linear": {"x": 5.0}, "angular": {"z": 0.0}})
    assert safe["linear"]["x"] == 0.5
    assert event.outcome == "clamped"
    assert event.applied is True


def test_middleware_clamps_negative_and_angular(safety_config_path):
    mw = SafetyMiddleware(config_path=safety_config_path)
    safe, event = mw.apply("/cmd_vel", {"linear": {"x": -3.0}, "angular": {"z": 9.0}})
    assert safe["linear"]["x"] == -0.5
    assert safe["angular"]["z"] == 1.0
    assert event.outcome == "clamped"


def test_middleware_within_limit_success_but_applied_true(safety_config_path):
    mw = SafetyMiddleware(config_path=safety_config_path)
    safe, event = mw.apply("/cmd_vel", {"linear": {"x": 0.3}, "angular": {"z": 0.0}})
    assert safe["linear"]["x"] == 0.3
    assert event.outcome == "success"
    assert event.applied is True  # layer ran even though nothing changed


def test_middleware_handles_partial_raw_dict(safety_config_path):
    # raw dict with no angular key must not crash and must still clamp linear.x
    mw = SafetyMiddleware(config_path=safety_config_path)
    safe, event = mw.apply("/cmd_vel", {"linear": {"x": 4.0}})
    assert safe["linear"]["x"] == 0.5
    assert "angular" not in safe
    assert event.outcome == "clamped"


def test_middleware_does_not_mutate_input(safety_config_path):
    mw = SafetyMiddleware(config_path=safety_config_path)
    original = {"linear": {"x": 5.0}, "angular": {"z": 0.0}}
    mw.apply("/cmd_vel", original)
    assert original["linear"]["x"] == 5.0  # caller's dict untouched


# --- SafetyMiddleware: workspace bounds (dormant for cmd_vel demo) ----------

def test_middleware_blocks_out_of_bounds_position(safety_config_path):
    mw = SafetyMiddleware(config_path=safety_config_path)
    _, event = mw.apply("/goal_pose", {"position": {"x": 99.0, "y": 0.0}})
    assert event.outcome == "blocked"
    assert event.applied is True


def test_middleware_allows_in_bounds_position(safety_config_path):
    mw = SafetyMiddleware(config_path=safety_config_path)
    _, event = mw.apply("/goal_pose", {"pose": {"position": {"x": 1.0, "y": -2.0}}})
    assert event.outcome == "success"


def test_middleware_passthrough_non_position_topic(safety_config_path):
    mw = SafetyMiddleware(config_path=safety_config_path)
    _, event = mw.apply("/some_topic", {"data": "hello"})
    assert event.outcome == "success"
    assert event.applied is False


# --- ConfirmationGate -------------------------------------------------------

def test_gate_raises_for_confirmation_required_service(safety_config_path):
    gate = ConfirmationGate(config_path=safety_config_path)
    with pytest.raises(ConfirmationRequired):
        gate.check("/robot/emergency_stop")


def test_gate_passes_for_unlisted_service(safety_config_path):
    gate = ConfirmationGate(config_path=safety_config_path)
    assert gate.check("/reset_simulation") is None


# --- CommandLogger ----------------------------------------------------------

def test_logger_writes_line_per_call(safety_config_path):
    logger = CommandLogger(config_path=safety_config_path)
    logger.log(tool="ros_publish_topic", args={"topic": "/cmd_vel"}, outcome="clamped",
               reason="Velocity clamped")
    logger.log(tool="ros_list_topics", args={}, outcome="success")
    lines = logger.path.read_text().strip().splitlines()
    assert len(lines) == 2
    assert "TOOL=ros_publish_topic" in lines[0]
    assert "OUTCOME=clamped" in lines[0]
    assert "ARGS=" in lines[0] and json.loads(lines[0].split("ARGS=")[1].split(" | ")[0])


# --- Tool-level: clamp is framing-independent (adversarial 1, 2, 4) ---------

@pytest.mark.parametrize("msg", [
    {"linear": {"x": 5.0}, "angular": {"z": 0.0}},   # authority-override value
    {"linear": {"x": 3.0}, "angular": {"z": 0.0}},   # "test mode" value
    {"linear": {"x": 4.0}, "angular": {"z": 0.0}},   # raw-dict routing value
])
def test_publish_cmd_vel_clamps_regardless_of_message(tools, fake_client, msg):
    result = tools["ros_publish_topic"](topic="/cmd_vel", message=msg)
    _assert_contract(result)
    assert result["status"] == "clamped"
    assert result["safety_applied"] is True
    published_msg = fake_client.published[0][2]
    assert published_msg["linear"]["x"] == 0.5


# --- Tool-level: confirmation gate (adversarial 5) --------------------------

def test_call_service_blocks_without_confirm(tools, fake_client):
    result = tools["ros_call_service"](service="/robot/emergency_stop")
    _assert_contract(result)
    assert result["status"] == "blocked"
    assert result["safety_applied"] is True
    assert "confirm=True" in result["message"]


def test_call_service_executes_with_confirm(tools, fake_client):
    result = tools["ros_call_service"](service="/robot/emergency_stop", confirm=True)
    _assert_contract(result)
    assert result["status"] == "success"
    assert result["safety_applied"] is True  # gated service, deliberately confirmed


def test_call_non_gated_service_needs_no_confirm(tools):
    result = tools["ros_call_service"](service="/reset_simulation")
    _assert_contract(result)
    assert result["status"] == "success"
    assert result["safety_applied"] is False


# --- Tool-level: every call is logged ---------------------------------------

def test_every_tool_call_is_logged(tools, safety_log_path):
    tools["ros_list_topics"]()
    tools["ros_publish_topic"](topic="/cmd_vel", message={"linear": {"x": 5.0}})
    tools["ros_call_service"](service="/robot/emergency_stop")
    lines = open(safety_log_path).read().strip().splitlines()
    tools_logged = [line.split("TOOL=")[1].split(" |")[0] for line in lines]
    assert "ros_list_topics" in tools_logged
    assert "ros_publish_topic" in tools_logged
    assert "ros_call_service" in tools_logged
