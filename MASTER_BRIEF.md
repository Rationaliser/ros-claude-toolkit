# ros-claude-toolkit — MASTER BRIEF
> Single source of truth. Update this file as decisions change. Never contradict it without logging the reason.

---

## Project Identity

**Name:** ros-claude-toolkit
**Type:** Open-source research project
**Tagline:** A safety-aware MCP server and Claude Skills suite for ROS 2 engineering
**Repo:** github.com/[username]/ros-claude-toolkit (to be created)
**License:** MIT
**Status:** Month 1 — Probation Period (Professor-sponsored)

---

## The Problem

Existing LLM–ROS integration tools are fragmented:
- **ROSA (NASA-JPL, 2024):** LangChain-based, not MCP-native, no Skills layer
- **Community MCP servers:** No safety layer, no Skills, no unified installer
- **ros2-engineering-skills:** Static SKILL.md only, no live MCP integration

No existing package combines: runtime bidirectional ROS 2 control + formalized safety constraints + Claude Skills that read live robot state.

---

## The Solution — Architecture

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

**Primary novel contribution:** The Safety Layer — velocity clamping, workspace boundary enforcement, confirmation gates for destructive operations, command logging. No existing tool formalizes this as reusable MCP middleware.

---

## Technical Decisions (Locked)

| Decision | Choice | Reason |
|---|---|---|
| ROS version target | ROS 2 only (Humble + Jazzy) | ROS 1 EOL 2025 |
| Month 1 transport | rosbridge WebSocket | Faster to POC; rewrite to rclpy Month 2 |
| Month 2+ transport | rclpy native | Lower latency, better safety layer control |
| MCP framework | FastMCP (Python) | Cleanest Python MCP server implementation |
| Primary simulation | Gazebo + TurtleBot3 | Widely available, reproducible across machines |
| Config format | YAML | Human-readable, easy for engineers to modify |
| Claude integration | Claude Code (Month 1 onward) | Claude Desktop has no Linux build (ADR-008) |

---

## Competitive Differentiation

| Feature | ROSA (NASA-JPL) | Community MCP | ros-claude-toolkit |
|---|---|---|---|
| Runtime Control | ✓ | ✓ | ✓ |
| Safety Layer | Partial | ✗ | ✓ |
| Claude Skills | ✗ | ✗ | ✓ |
| Single Installer | ✗ | ✗ | ✓ |
| ROS 2 Native (rclpy) | ✗ | Partial | ✓ |
| MCP-native | ✗ | ✓ | ✓ |

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

## Month 1 — Locked Scope (Probation Period)

**Goal:** Make Claude control a simulated robot through natural language, safely, in a way the professor can watch live.

### MCP Tools to Build (Nothing More)
```
ros_list_topics()     → active topics + message types
ros_echo_topic()      → last N messages from a topic
ros_publish_topic()   → publish message to topic
ros_list_services()   → available services
ros_call_service()    → call service with arguments
ros_get_param()       → read parameter
ros_set_param()       → set parameter
```

### Safety Layer MVP
```yaml
# safety_config.yaml
velocity_limits:
  linear_x:  max: 0.5    # m/s
  angular_z: max: 1.0    # rad/s

confirmation_required:
  - /robot/emergency_stop

workspace_bounds:
  x: [-5.0, 5.0]
  y: [-5.0, 5.0]
```

Three behaviors:
1. Velocity clamping on all cmd_vel publishes
2. Confirmation gate on blacklisted services
3. Command logging with timestamp

### Demo Script (End of Month 1)
```
Step 1: "List all active topics"           → Claude reads live ROS 2 system
Step 2: "Move the robot forward at 2 m/s"  → Clamped to 0.5, Claude explains why
Step 3: "Move the robot forward at 0.3 m/s"→ Executes, robot moves in Gazebo
Step 4: "Call the emergency stop service"  → Confirmation gate triggers
Step 5: "Confirm and call it"              → Executes
```

### Month 1 Success Criteria
- [ ] Runs on someone else's machine (not just yours)
- [ ] Safety layer cannot be bypassed through normal prompting
- [ ] Demo is recorded and repo is public
- [ ] README: install in under 20 minutes

---

## Known Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| asyncio + rclpy spin conflict | High | Use rosbridge in Month 1, rclpy in Month 2 |
| Scope creep | High | Refer to MONTH1_SCOPE.md, say no to everything else |
| Gazebo cold start in demo | Medium | Pre-load simulation before professor meeting |
| Safety layer bypassable | Medium | Adversarial prompt test before demo |

---

## People

| Person | Role | Context |
|---|---|---|
| Vedant (Rationaliser) | Builder | M.Eng. Robotics, DIT Germany |
| Professor [Name] | Advisor + Sponsor | Robotics dept, DIT. Agreed to pay post-POC |

---

## Out of Scope Until Further Notice
- ROS 1 support
- Actions server (Month 2)
- Custom message type introspection (Month 2)
- URDF/xacro skill (Month 5)
- Nav2 skill (Month 5)
- Docker container (Month 6)
- Research paper writing

---

## Key References
- ROSA (NASA-JPL): https://github.com/nasa-jpl/rosa
- robotmcp/ros-mcp-server: https://github.com/robotmcp/ros-mcp-server
- LCAS/ros2_mcp: https://github.com/LCAS/ros2_mcp
- FastMCP docs: https://gofastmcp.com
- ROSBag MCP paper: (peer-reviewed, Nov 2025)
