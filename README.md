# ros-llm-toolkit

> A safety-aware MCP server and Claude Skills suite for ROS 2 engineering.

`ros-llm-toolkit` lets Claude inspect and control a ROS 2 system through natural
language, with a safety layer that clamps velocities, gates destructive operations behind
confirmation, and logs every command. Month 1 targets a live demo: Claude driving a
TurtleBot3 in Gazebo, safely.

**Status:** Month 1 — Proof of Concept · ROS 2 Humble / Jazzy · License: MIT

---

## Prerequisites

You need a working ROS 2 desktop install (**Humble** or **Jazzy**) with TurtleBot3, Gazebo,
and rosbridge. These are **not** installed by `install.sh` — install them first.

**ROS 2 Humble (Ubuntu 22.04):**

```bash
sudo apt update
sudo apt install ros-humble-desktop ros-humble-turtlebot3* \
                 ros-humble-rosbridge-suite ros-humble-gazebo-ros-pkgs
```

**ROS 2 Jazzy (Ubuntu 24.04):**

```bash
sudo apt update
sudo apt install ros-jazzy-desktop ros-jazzy-turtlebot3* \
                 ros-jazzy-rosbridge-suite ros-jazzy-gazebo-ros-pkgs
```

Also required: **Python 3.10+**, `python3-venv`, and `git`. Set the robot model before
launching the simulation:

```bash
export TURTLEBOT3_MODEL=burger
```

---

## Install

Three commands. `install.sh` creates a repo-local `.venv`, installs the toolkit's Python
dependencies, verifies rosbridge, and generates `.mcp.json` with absolute paths for Claude Code.

```bash
git clone https://github.com/Rationaliser/ros-llm-toolkit.git
cd ros-llm-toolkit
bash install.sh
```

On a machine that already has the prerequisites above, this completes in **under 20 minutes**
(most of that is the one-time `pip` download). Re-running `install.sh` is safe — it reuses the
existing `.venv` and regenerates `.mcp.json`.

---

## Usage

Bring up the stack in three terminals:

```bash
# Terminal 1 — rosbridge
ros2 launch rosbridge_server rosbridge_websocket_launch.xml

# Terminal 2 — Gazebo + TurtleBot3
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# Terminal 3 — MCP server
.venv/bin/python mcp/server.py
```

Open **Claude Code** in the repo directory. It reads `.mcp.json` automatically and exposes the
seven `ros_*` tools. Then try the demo prompts:

```
1. "What topics are active on the robot?"
   → Claude lists /cmd_vel, /odom, /scan, /tf, ...

2. "What is the robot's current position?"
   → Claude echoes /odom

3. "Move the robot forward at 2 metres per second"
   → Safety layer clamps to 0.22 m/s; robot moves slowly; Claude explains the clamp

4. "Move the robot forward at 0.2 metres per second"
   → Executes without clamping; robot moves

5. "Call the emergency stop service"
   → Confirmation gate triggers; Claude asks you to confirm

6. "Confirm"
   → Service is called; robot stops
```

---

## Safety layer

The safety layer is the toolkit's core contribution — reusable MCP middleware that every
publish and service call passes through. It reads `config/safety_config.yaml` on every tool
call (edit the YAML; changes take effect on the next call — code never writes to it).

- **Velocity clamping** — publishes to `/cmd_vel` are clamped to the configured limits:
  `linear.x` to ±0.22 m/s and `angular.z` to ±1.0 rad/s by default. Claude is told the original
  and clamped values.
- **Confirmation gate** — services in `confirmation_required` (e.g. `/robot/emergency_stop`)
  are blocked unless the call passes `confirm=True`.
- **Workspace bounds** — position-bearing publishes are checked against `workspace_bounds`.
- **Command audit log** — every tool invocation is appended to `logs/commands.log`.

Example clamp, straight from `logs/commands.log`:

```
[2026-07-01T09:21:11.034771+00:00] TOOL=ros_publish_topic | ARGS={"message": {"angular": {"x": 0, "y": 0, "z": 0}, "linear": {"x": 0.6, "y": 0, "z": 0}}, "msg_type": "geometry_msgs/Twist", "topic": "/cmd_vel"} | OUTCOME=clamped | REASON=Velocity clamped: linear.x 0.6 → 0.22 (config limit: 0.22)
```

The safety layer cannot be bypassed through prompting — attempts are refused and logged.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  SKILLS LAYER  (Claude Code / claude.ai)         │
│  ros2-debug | ros2-launch | ros2-urdf | ros2-nav2│
├─────────────────────────────────────────────────┤
│  MCP SERVER LAYER  (runtime bridge)              │
│  Runtime Control | Safety Layer | Diagnostics    │
│  ROSBag Module                                   │
├─────────────────────────────────────────────────┤
│  ROS 2 ENVIRONMENT                               │
│  Gazebo Simulation | Physical Robot              │
│  Humble / Jazzy / Iron                           │
└─────────────────────────────────────────────────┘
```

The **Safety Layer** is the novel contribution: velocity clamping, workspace boundary
enforcement, confirmation gates, and command logging as reusable MCP middleware.

---

## Roadmap

| Month | Phase | Key Deliverable |
|---|---|---|
| **1** | **Proof of Concept** | **MCP server + safety layer MVP + Gazebo demo** |
| 2 | Alpha Core | rclpy rewrite, custom messages, actions support |
| 3 | Safety + Diagnostics | Full permission profiles, TF inspector, QoS detector |
| 4 | Skills v1 | ros2-debug + ros2-launch (MCP-connected) |
| 5 | Skills v2 + Packaging | ros2-urdf + ros2-nav2, single installer |
| 6 | v1.0 Release | Docker, docs, ROS Discourse launch |

---

## License

[MIT](LICENSE)
