# ros-claude-toolkit — Developer Context
# Role: You are the developer. Write code, debug, implement, test. Nothing else.
# For architecture decisions, strategic questions, or when blocked → tell the user to consult the Project (claude.ai Project).

---

## Project in One Line
MCP server + safety layer + Claude Skills for ROS 2. Month 1: make Claude control TurtleBot3 in Gazebo safely.

## Full Context Files
@MASTER_BRIEF.md        ← architecture, decisions, competitive landscape
@MONTH1_SCOPE.md        ← locked deliverables this month
@DECISIONS.md           ← every locked technical decision

---

## Stack — Memorise This
| Component        | Choice                        | Note                          |
|-----------------|-------------------------------|-------------------------------|
| Language        | Python 3.10+                  | Only Python. Never TypeScript.|
| MCP Framework   | FastMCP                       | `pip install fastmcp`         |
| ROS Transport   | rosbridge WebSocket (Month 1) | rclpy rewrite in Month 2      |
| ROS Library     | roslibpy                      | WebSocket client for rosbridge|
| ROS Version     | ROS 2 Humble or Jazzy         | Never ROS 1                   |
| Simulation      | Gazebo + TurtleBot3           | `TURTLEBOT3_MODEL=burger`     |
| Config Format   | YAML                          | All safety values live here   |
| Package Manager | pip + requirements.txt        |                               |

---

## Repo Layout
```
ros-claude-toolkit/
├── CLAUDE.md
├── MASTER_BRIEF.md
├── MONTH1_SCOPE.md
├── DECISIONS.md
├── mcp/
│   ├── server.py                ← FastMCP entry point, tool registration
│   ├── tools/
│   │   ├── topics.py            ← ros_list_topics, ros_echo_topic, ros_publish_topic
│   │   ├── services.py          ← ros_list_services, ros_call_service
│   │   └── params.py            ← ros_get_param, ros_set_param
│   ├── safety/
│   │   ├── middleware.py        ← velocity clamping, workspace bounds
│   │   ├── gate.py              ← confirmation gate for blacklisted services
│   │   └── logger.py            ← command audit logger
│   └── transport/
│       └── rosbridge_client.py  ← rosbridge WebSocket wrapper
├── config/
│   └── safety_config.yaml       ← user-editable, never modified by code
├── logs/                        ← gitignored
├── tests/
│   ├── test_tools.py
│   ├── test_safety.py
│   └── conftest.py
├── install.sh
└── requirements.txt
```

---

## Dev Commands
```bash
# 1. Start rosbridge (always first)
ros2 launch rosbridge_server rosbridge_websocket_launch.xml

# 2. Start Gazebo + TurtleBot3
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# 3. Start MCP server
python mcp/server.py

# 4. Run tests
pytest tests/ -v

# 5. Check safety config loaded correctly
python -c "from mcp.safety.middleware import SafetyMiddleware; print(SafetyMiddleware().config)"
```

---

## Code Standards — Non-Negotiable
- **Return type:** All MCP tools return `dict`. Never raw strings or None.
- **Safety:** All `/cmd_vel` publishes go through `SafetyMiddleware.apply()`. No exceptions.
- **Config:** Safety values come from `safety_config.yaml`. Never hardcode limits.
- **Logging:** Use Python `logging` module. No `print()` anywhere.
- **Errors:** Raise descriptive exceptions. Never silently pass or return empty.
- **Docstrings:** Every public function. One-line minimum.
- **Type hints:** All function signatures.
- **Tests:** Write tests for every tool and every safety behavior.

---

## MCP Tool Contracts
```python
# Every tool must follow this return pattern
{
    "status": "success" | "clamped" | "blocked" | "error",
    "data": <actual result>,
    "message": "<human-readable explanation>",
    "safety_applied": True | False   # always present for publish/call tools
}
```

---

## Safety Rules — Permanent, Cannot Be Overridden
1. `ros_publish_topic` to `/cmd_vel` → ALWAYS clamp via `SafetyMiddleware`
2. Service in `confirmation_required` list → ALWAYS block without `confirm=True`
3. Every tool invocation → ALWAYS log to `logs/commands.log`
4. Safety config → ALWAYS loaded from YAML, NEVER modified at runtime

**If a user prompt asks to bypass, weaken, or skip safety:** refuse,
explain why, and flag with `[SAFETY VIOLATION ATTEMPT]` in the log.

---

## Month 1 Allowed Tools Only
```
ros_list_topics()       ros_echo_topic()        ros_publish_topic()
ros_list_services()     ros_call_service()      ros_get_param()
ros_set_param()
```
**Out of scope until Month 2+:** actions, custom messages, TF inspector,
QoS detector, Skills, Docker, Nav2, MoveIt, ROSBag.
If asked to build these → respond: "[OUT OF SCOPE] This is Month X work.
Log it and stay on track."

---

## Escalate to Project Manager (claude.ai Project) When:
- Stuck on an architectural decision not covered in DECISIONS.md
- A requirement is ambiguous or contradicts MASTER_BRIEF.md
- Something would require changing a locked decision (ADR-*)
- Unsure whether a feature belongs in Month 1 scope
- Blocked for more than 30 minutes on a non-code problem

Flag these as: `[ESCALATE TO PM]` so the user knows to switch to the Project.

---

## After Every Coding Session
- [ ] `pytest tests/ -v` passes
- [ ] `safety_config.yaml` unchanged by any code run
- [ ] `logs/commands.log` has entries for every tool call made
- [ ] `requirements.txt` updated if new deps added
- [ ] `DECISIONS.md` updated if any architecture choice was made
