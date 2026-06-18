# Month 1 — Locked Execution Scope
> Probation period. Professor sponsorship contingent on working demo.
> This file is a contract with yourself. Do not add to it mid-month.

---

## North Star
**By Day 30:** Claude controls a TurtleBot3 in Gazebo through natural language. The safety layer clamps a velocity command live. The professor watches it happen.

---

## Week 1 — Environment + Audit (Days 1–7)

### Tasks
- [ ] ROS 2 (Humble or Jazzy) + Gazebo running locally
- [ ] TurtleBot3 simulation launching clean
- [ ] Clone and run `robotmcp/ros-mcp-server` end-to-end
- [ ] Clone and run `LCAS/ros2_mcp` end-to-end
- [ ] Document failure points of both (create `AUDIT.md`)
- [ ] **DECISION:** rosbridge vs rclpy — commit by Day 7 (default: rosbridge)
- [ ] GitHub repo created: `ros-claude-toolkit`, MIT license, README stub
- [ ] FastMCP installed and hello-world MCP server running in Claude Desktop

### Hard Stop
Do not enter Week 2 without:
- ROS 2 + Gazebo working
- Transport decision made
- Repo live on GitHub

### Environment Setup Reference
```bash
# ROS 2 Humble (Ubuntu 22.04)
sudo apt install ros-humble-desktop ros-humble-turtlebot3*
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# rosbridge
sudo apt install ros-humble-rosbridge-suite
ros2 launch rosbridge_server rosbridge_websocket_launch.xml

# FastMCP
pip install fastmcp
```

---

## Week 2 — Core MCP Server (Days 8–14)

### Tasks
- [ ] Implement `ros_list_topics()` — returns topic names + message types
- [ ] Implement `ros_echo_topic()` — returns last N messages
- [ ] Implement `ros_publish_topic()` — publishes to any topic
- [ ] Implement `ros_list_services()` — returns available services
- [ ] Implement `ros_call_service()` — calls service with args
- [ ] Implement `ros_get_param()` — reads parameter
- [ ] Implement `ros_set_param()` — sets parameter
- [ ] Claude Desktop config updated, all 7 tools visible
- [ ] Test: Claude can list topics from live TurtleBot3 simulation
- [ ] Test: Claude can move TurtleBot3 via `ros_publish_topic` to `/cmd_vel`

### Definition of Done — Week 2
Claude Desktop prompt: *"What topics are available on the robot?"*
→ Returns real topic list from running Gazebo simulation.

Claude Desktop prompt: *"Move the robot forward slowly"*
→ TurtleBot3 moves in Gazebo.

### File Structure by End of Week 2
```
ros-claude-toolkit/
├── mcp/
│   ├── server.py          ← FastMCP server entry point
│   ├── tools/
│   │   ├── topics.py      ← list, echo, publish
│   │   ├── services.py    ← list, call
│   │   └── params.py      ← get, set
│   └── rosbridge_client.py
├── config/
│   └── safety_config.yaml  ← stub for Week 3
├── README.md
└── requirements.txt
```

---

## Week 3 — Safety Layer MVP (Days 15–21)

### Tasks
- [ ] `safety_config.yaml` schema defined and documented
- [ ] Velocity clamping middleware — wraps `ros_publish_topic` for `/cmd_vel`
- [ ] Workspace boundary check — rejects publishes outside configured bounds
- [ ] Confirmation gate — blocks blacklisted service calls without `confirm: true`
- [ ] Command logger — writes every Claude-issued command to `logs/commands.log`
- [ ] Test: Send `linear_x: 2.0` → clamped to `0.5`, Claude told why
- [ ] Test: Call `/emergency_stop` without confirmation → blocked with explanation
- [ ] Test: Call `/emergency_stop` with confirmation → executes
- [ ] Adversarial prompt test: Try to convince Claude to bypass safety in 5 different ways

### Safety Config Schema
```yaml
velocity_limits:
  linear_x:
    max: 0.5      # m/s — hard ceiling
    min: -0.5
  angular_z:
    max: 1.0      # rad/s
    min: -1.0

confirmation_required:
  - /robot/emergency_stop
  - /robot/arm/move_to_pose   # placeholder for future

workspace_bounds:
  x: [-5.0, 5.0]   # metres from origin
  y: [-5.0, 5.0]

logging:
  enabled: true
  path: logs/commands.log
  format: "[{timestamp}] {tool} | {args} | {outcome}"
```

### Definition of Done — Week 3
Prompt: *"Move the robot forward at 5 m/s"*
→ Velocity clamped to 0.5 m/s, robot moves, Claude responds:
*"Velocity was clamped from 5.0 to 0.5 m/s (safety limit). Command executed."*

---

## Week 4 — Integration + Demo Polish (Days 22–30)

### Tasks
- [ ] `install.sh` — detects ROS distro, installs deps, generates `claude_desktop_config.json`
- [ ] README complete: prerequisites → install → 3 demo commands → screenshot
- [ ] All 7 MCP tools + safety layer working together without manual intervention
- [ ] Demo script rehearsed minimum 3 times (Gazebo pre-loaded)
- [ ] 3-minute screen recording of full demo script
- [ ] Repo public, clean commit history, no debug prints left in code

### install.sh Behaviour
```bash
#!/bin/bash
# Detects ROS distro
# Installs: pip install fastmcp roslibpy pyyaml
# Generates claude_desktop_config.json at correct path
# Validates rosbridge is available
# Prints: "Setup complete. Launch with: python mcp/server.py"
```

### Demo Script (Rehearse This)
```
[Gazebo pre-loaded with TurtleBot3]

1. "What topics are active on the robot?"
   → Claude lists: /cmd_vel, /odom, /scan, /tf ...

2. "What is the robot's current position?"
   → Claude echoes /odom

3. "Move the robot forward at 2 metres per second"
   → Safety layer clamps to 0.5 m/s
   → Robot moves slowly in Gazebo
   → Claude: "Clamped from 2.0 to 0.5 m/s per safety config"

4. "Move the robot forward at 0.3 metres per second"
   → Executes without clamping
   → Robot moves in Gazebo

5. "Call the emergency stop service"
   → Confirmation gate triggers
   → Claude: "This is a confirmation-required operation. Reply with confirm to proceed."

6. "Confirm"
   → Service called
   → Robot stops
```

### Month 1 Success Criteria Checklist
- [ ] Runs on a machine that is not yours (test on lab computer or VM)
- [ ] Safety layer cannot be bypassed through 5 adversarial prompts
- [ ] Demo recorded (upload to YouTube unlisted or GitHub repo)
- [ ] README install time < 20 minutes (time it yourself)
- [ ] GitHub repo public with clean history

---

## What Is Explicitly NOT Month 1 Work

If you find yourself building any of the following, stop immediately and return to this file:

- ❌ Actions support
- ❌ Custom message type parsing
- ❌ TF tree inspector
- ❌ QoS mismatch detector
- ❌ Any SKILL.md files
- ❌ Docker container
- ❌ Nav2 or MoveIt integration
- ❌ ROSBag module
- ❌ Web UI or dashboard
- ❌ Research paper writing

---

## Daily Check-in Questions

Ask yourself these every morning:
1. Am I working on something in the locked scope?
2. Will this directly contribute to the 5-step demo?
3. Am I on track for the week's definition of done?

If the answer to 1 or 2 is no — stop and redirect.
