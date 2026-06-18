# Reference Server Audit
> Week 1, Day 1. Tested on Ubuntu 22.04, ROS 2 Humble, Python 3.10.12, numpy 2.2.6.
> rosbridge running locally (127.0.0.1:9090, confirmed via curl + rosapi service list).
> Gazebo + TurtleBot3 NOT launched during this audit — only rosbridge + rosapi are live.
> For each repo: install attempted, server started, tool calls driven via MCP stdio/HTTP.

---

## 1. robotmcp/ros-mcp-server

**Repo:** https://github.com/robotmcp/ros-mcp-server  
**Transport:** rosbridge WebSocket (connects to port 9090 over the network)  
**MCP framework:** FastMCP 3.4.2 (stdio + HTTP + streamable-HTTP)  
**Language:** Python

### Install steps

```bash
cd reference/ros-mcp-server
python3 -m venv .venv-rosmcp
.venv-rosmcp/bin/pip install .   # ← installs ros-mcp entry point
```

**Result:** ✅ Installed cleanly. Only noise: `generate-parameter-library-py` (system ROS package) complains about missing jinja2/typeguard — unrelated to ros-mcp, no effect on runtime.

### End-to-end test

Drove via MCP stdio protocol (Python subprocess + threading):

```
initialize          → ✅ protocolVersion 2024-11-05, server ros-mcp-server 3.4.2
connect_to_robot    → ✅ WebSocket connected to 127.0.0.1:9090
                         ping: 0.02 ms, port open, "Fully_accessible"
get_nodes           → ✅ ["/rosbridge_websocket", "/rosapi", "/rosapi_params"]
get_topics          → ✅ 4 topics: /client_count, /connected_clients,
                         /parameter_events, /rosout
```

**Failure point:** None with rosbridge running. All 4 calls succeeded on the first attempt.

**Note — requires rosapi:** The rosbridge launch file (`ros2 launch rosbridge_server rosbridge_websocket_launch.xml`) starts both `rosbridge_websocket` and `rosapi_node`. Tools like `get_nodes` use rosapi services; launching rosbridge with `ros2 run` (without the launch file) omits rosapi and would cause every introspection tool to fail.

### Tools available

31 tools across: actions, connect/ping, nodes, parameters, services, topics, publish/subscribe, image capture. Full list includes `publish_for_durations`, `subscribe_once`, `subscribe_for_duration`, `get_image`, `drive_robot` (via topics).

### Safety layer

❌ **None.** No velocity clamping, no confirmation gate, no command logging. `publish_for_durations` accepts arbitrary velocities without bounds checking.

### ROS 2 Humble compatibility

✅ Works on Humble. Minor warnings about `default_call_service_timeout` and `call_services_in_new_thread` defaults (will change in Jazzy) — benign on Humble.

### Install friction

Low. `pip install ros-mcp` or `pip install .` from source. No ROS workspace build needed. Requires rosbridge on the robot side (one `apt install` + one `ros2 launch`).

---

## 2. LCAS/ros2_mcp

**Repo:** https://github.com/LCAS/ros2_mcp  
**Transport:** rclpy native (direct DDS, not rosbridge). Exposes SSE HTTP endpoint on port 8000.  
**MCP framework:** FastMCP (older API — `mcp[cli]` pinned, not `fastmcp`)  
**Language:** Python + ROS 2 colcon package

### Install steps attempted

The README requires a colcon workspace build:
```bash
cd ~/ros2_workspace/src
git clone ...
cd ../..
rosdep install -i --from-paths src/
colcon build
source install/setup.bash
ros2 run ros2_mcp ros2_mcp_server
```

Attempted shortcut: venv with `--system-site-packages` (to inherit ROS Python bindings):
```bash
python3 -m venv .venv-lcas --system-site-packages
.venv-lcas/bin/pip install "mcp[cli]" opencv-python
```

**rclpy import:** ✅ Succeeded — node creation and `get_node_names()` worked against live ROS 2.

**cv_bridge import:** ⚠️ NumPy ABI mismatch. cv_bridge (Humble) was compiled against NumPy 1.x; system has NumPy 2.2.6. Error: `AttributeError: _ARRAY_API not found`. Non-fatal warning on import but causes crash at runtime when image tools are used.

### End-to-end test

```bash
python src/ros2_mcp/ros2_mcp/ros2_mcp_server.py
```

**Failure — two independent errors:**

1. **cv_bridge crash on import** (NumPy ABI incompatibility):
   ```
   AttributeError: _ARRAY_API not found
   ```
   Any tool touching `sensor_msgs/Image` would fail. Core tools (`list_topics`, `topic_echo`, `drive_robot`) are unaffected by cv_bridge at import time — they would work if the server started.

2. **FastMCP API mismatch (hard failure, server does not start):**
   ```
   TypeError: FastMCP.run() got an unexpected keyword argument 'host'
   ```
   The code calls `mcp.run(transport="sse", host="0.0.0.0")`. Current FastMCP (3.4.2) removed the `host` kwarg from `run()`. This is a **breaking API change** introduced between the FastMCP version used when the repo was written and the current release. The server exits immediately.

**Server never came up. No tool calls possible without patching.**

### To fix (not our job — audit only)

- Pin `fastmcp<2.0` or change `mcp.run(transport="sse", host="0.0.0.0")` to the current API.
- Downgrade numpy to `<2` OR install `ros-humble-cv-bridge` built against NumPy 2 (unavailable in apt as of this audit).

### Tools available (from source review)

6 tools: `topic_echo`, `get_image`, `get_camera_info`, `list_topics`, `introspect_interface`, `drive_robot`. Also 4 prompts for robot state analysis.

### Safety layer

❌ **None.** `drive_robot` publishes directly to `/cmd_vel` with no velocity clamping, no confirmation, no logging.

### ROS 2 Humble compatibility

⚠️ Partial. rclpy works. cv_bridge fails due to numpy ABI mismatch (system numpy 2.2.6 vs Humble cv_bridge compiled for numpy 1.x). FastMCP API mismatch prevents startup entirely.

### Install friction

High. Requires: colcon workspace build OR manual NumPy/FastMCP version pinning. Primary deployment path is Docker (maintained by authors). No single-command install outside Docker.

---

## Comparison Summary

| Feature | robotmcp/ros-mcp-server | LCAS/ros2_mcp | ros-claude-toolkit (target) |
|---|---|---|---|
| Transport | rosbridge WebSocket | rclpy native (DDS) | rosbridge (Month 1), rclpy (Month 2) |
| MCP-native | ✅ | ✅ | ✅ |
| Safety layer | ❌ | ❌ | ✅ velocity clamp + gate + log |
| ROS 2 Humble | ✅ | ⚠️ partial (numpy/fastmcp broken) | ✅ |
| Install friction | Low (pip install) | High (colcon or Docker) | Low (install.sh target) |
| Runtime control | ✅ full | ✅ full (if running) | ✅ |
| Publish to cmd_vel | ✅ unclamped | ✅ unclamped | ✅ clamped via SafetyMiddleware |
| Runs without Gazebo | ✅ (rosbridge only) | ❌ server won't start | ✅ (same as ros-mcp) |
| Command logging | ❌ | ❌ | ✅ logs/commands.log |
| Confirmation gate | ❌ | ❌ | ✅ blacklist config |

## Key Findings for ros-claude-toolkit

1. **The safety gap is real.** Both existing tools publish velocities without any bounds checking. Our `SafetyMiddleware` fills a genuine missing feature, not a duplicate one.

2. **robotmcp is the closest competitor.** Well-maintained, installable via pip, Claude Code support documented, works on Humble. Our differentiation must be the safety layer + Skills layer — not install ease alone.

3. **rosbridge is the right Month 1 choice** (confirmed ADR-002). LCAS/ros2_mcp shows the fragility of rclpy in a vanilla Python environment — numpy ABI mismatches, FastMCP API churn. rosbridge isolates the Python process from ROS ABI entirely.

4. **FastMCP API is moving fast.** LCAS broke because of a `host` kwarg removal between releases. Pin versions explicitly in `requirements.txt` (already done: `fastmcp>=2.0,<4.0`).
