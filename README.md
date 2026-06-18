# ros-claude-toolkit

> A safety-aware MCP server and Claude Skills suite for ROS 2 engineering.

**Status:** Month 1 — Proof of Concept (in progress) · ROS 2 Humble · License: MIT

`ros-claude-toolkit` lets Claude inspect and control a ROS 2 system through natural
language, with a safety layer that clamps velocities, gates destructive operations behind
confirmation, and logs every command. Month 1 targets a live demo: Claude driving a
TurtleBot3 in Gazebo, safely.

## Architecture (target)

```
Skills Layer   →  ros2-debug | ros2-launch | ros2-urdf | ros2-nav2   (later months)
MCP Server     →  Runtime Control · Safety Layer · Diagnostics
ROS 2          →  Gazebo Simulation / Physical Robot  (Humble / Jazzy)
```

The **Safety Layer** is the novel contribution: velocity clamping, workspace bounds,
confirmation gates, and command logging as reusable MCP middleware.

## Status / Roadmap

| Month | Phase | Deliverable |
|---|---|---|
| **1** | **Proof of Concept** | **MCP server + safety layer MVP + Gazebo demo** |
| 2 | Alpha Core | rclpy rewrite, custom messages, actions |
| 3 | Safety + Diagnostics | permission profiles, TF inspector, QoS detector |
| 4–5 | Skills | ros2-debug, ros2-launch, ros2-urdf, ros2-nav2 |
| 6 | v1.0 | Docker, docs, ROS Discourse launch |

## Install

_Coming in Week 4 — single-command setup via `install.sh`._

## Demo

_3-minute walkthrough coming at the end of Month 1._

## License

[MIT](LICENSE)
