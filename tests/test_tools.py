"""Tests for the 7 Month-1 MCP tools (happy path + edge cases).

Safety-behavior tests (clamping, gate, logging) are deferred to Week 3; this suite only
asserts the no-op safety hook is present and reported on publish.
"""

CONTRACT_KEYS = {"status", "data", "message", "safety_applied"}


def _assert_contract(result: dict) -> None:
    """Every tool must return the 4-key contract dict."""
    assert isinstance(result, dict)
    assert CONTRACT_KEYS.issubset(result.keys())
    assert isinstance(result["safety_applied"], bool)


# --- ros_list_topics --------------------------------------------------------

def test_ros_list_topics_happy_path(tools):
    result = tools["ros_list_topics"]()
    _assert_contract(result)
    assert result["status"] == "success"
    assert result["data"]["count"] == 3
    assert "/cmd_vel" in result["data"]["topics"]
    assert result["safety_applied"] is False


# --- ros_echo_topic ---------------------------------------------------------

def test_ros_echo_topic_resolves_type_and_returns_messages(tools):
    result = tools["ros_echo_topic"](topic="/cmd_vel", count=1)
    _assert_contract(result)
    assert result["status"] == "success"
    assert result["data"]["type"] == "geometry_msgs/Twist"
    assert len(result["data"]["messages"]) == 1


def test_ros_echo_topic_empty_topic_is_error(tools):
    result = tools["ros_echo_topic"](topic="")
    _assert_contract(result)
    assert result["status"] == "error"


def test_ros_echo_topic_unresolvable_type_is_error(tools):
    result = tools["ros_echo_topic"](topic="/unknown_topic")
    _assert_contract(result)
    assert result["status"] == "error"


# --- ros_publish_topic ------------------------------------------------------

def test_ros_publish_topic_publishes_and_reports_safety_hook(tools, fake_client):
    msg = {"linear": {"x": 0.2}, "angular": {"z": 0.0}}
    result = tools["ros_publish_topic"](topic="/cmd_vel", message=msg)
    _assert_contract(result)
    assert result["status"] == "success"
    # safety hook is present but a no-op in Week 2
    assert result["safety_applied"] is False
    # publish actually reached the transport with the resolved type
    assert fake_client.published == [("/cmd_vel", "geometry_msgs/Twist", msg)]


def test_ros_publish_topic_default_type_for_cmd_vel(tools, fake_client):
    # topic_type returns "" for this name, but the cmd_vel fallback supplies the type
    result = tools["ros_publish_topic"](topic="/robot/cmd_vel", message={"linear": {"x": 0.1}})
    _assert_contract(result)
    assert result["status"] == "success"
    assert fake_client.published[0][1] == "geometry_msgs/Twist"


def test_ros_publish_topic_empty_topic_is_error(tools, fake_client):
    result = tools["ros_publish_topic"](topic="", message={"linear": {"x": 0.1}})
    _assert_contract(result)
    assert result["status"] == "error"
    assert fake_client.published == []


# --- ros_list_services ------------------------------------------------------

def test_ros_list_services_happy_path(tools):
    result = tools["ros_list_services"]()
    _assert_contract(result)
    assert result["status"] == "success"
    assert result["data"]["count"] == 2


# --- ros_call_service -------------------------------------------------------

def test_ros_call_service_resolves_type(tools):
    result = tools["ros_call_service"](service="/reset_simulation")
    _assert_contract(result)
    assert result["status"] == "success"
    assert result["data"]["type"] == "std_srvs/Empty"


def test_ros_call_service_unresolvable_type_is_error(tools):
    result = tools["ros_call_service"](service="/mystery_service")
    _assert_contract(result)
    assert result["status"] == "error"


# --- ros_get_param / ros_set_param -----------------------------------------

def test_ros_get_param_happy_path(tools):
    result = tools["ros_get_param"](name="/use_sim_time")
    _assert_contract(result)
    assert result["status"] == "success"
    assert result["data"]["value"] is True


def test_ros_get_param_empty_name_is_error(tools):
    result = tools["ros_get_param"](name="")
    _assert_contract(result)
    assert result["status"] == "error"


def test_ros_set_param_writes_value(tools, fake_client):
    result = tools["ros_set_param"](name="/max_speed", value=0.4)
    _assert_contract(result)
    assert result["status"] == "success"
    assert fake_client.params["/max_speed"] == 0.4
