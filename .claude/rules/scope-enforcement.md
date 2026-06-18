# Rule: Month 1 Scope Enforcement
# Active until Day 30 demo is delivered and professor approves Month 2.

## In Scope — Build Only These
| Tool | File | Status |
|------|------|--------|
| ros_list_topics | mcp/tools/topics.py | Build |
| ros_echo_topic | mcp/tools/topics.py | Build |
| ros_publish_topic + safety | mcp/tools/topics.py + safety/ | Build |
| ros_list_services | mcp/tools/services.py | Build |
| ros_call_service + gate | mcp/tools/services.py + safety/ | Build |
| ros_get_param | mcp/tools/params.py | Build |
| ros_set_param | mcp/tools/params.py | Build |
| Safety middleware | mcp/safety/middleware.py | Build |
| Confirmation gate | mcp/safety/gate.py | Build |
| Command logger | mcp/safety/logger.py | Build |
| rosbridge client | mcp/transport/rosbridge_client.py | Build |
| install.sh | / | Build |
| README.md | / | Build |
| Tests for all above | tests/ | Build |

## Out of Scope — Refuse and Log
If the user asks to implement any of the following, respond with:
"[OUT OF SCOPE — Month {N}] Noted. Focus is on the Day 30 demo.
I'll add this to the backlog: {feature}"

| Feature | Target Month |
|---------|-------------|
| ROS 2 Actions | 2 |
| Custom message type introspection | 2 |
| rclpy native transport | 2 |
| TF tree inspector | 3 |
| QoS mismatch detector | 3 |
| ros2-debug Skill | 4 |
| ros2-launch Skill | 4 |
| ros2-urdf Skill | 5 |
| Nav2 / MoveIt integration | 5 |
| ROSBag module | 5 |
| Docker container | 6 |
| Web UI / dashboard | 6 |

## Escalate Scope Disputes to PM
If the user insists on out-of-scope work and won't accept the redirect:
"[ESCALATE TO PM] This scope question should be decided in the Claude Project,
not here. The PM has the full roadmap context."
