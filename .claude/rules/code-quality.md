# Rule: Code Quality Standards

## Python Style
- Type hints on all function signatures — no exceptions
- Docstrings on all public functions (one-line minimum)
- `logging` module only — zero `print()` statements in production code
- Constants in UPPER_SNAKE_CASE at module level or in config
- Max function length: 40 lines. If longer, split it.

## Error Handling
```python
# CORRECT
def ros_call_service(service: str, args: dict, confirm: bool = False) -> dict:
    if not rosbridge_client.is_connected():
        raise ConnectionError("rosbridge WebSocket not connected. "
                              "Run: ros2 launch rosbridge_server rosbridge_websocket_launch.xml")

# WRONG
def ros_call_service(service, args):
    try:
        ...
    except:
        return {}   # never silently fail
```

## Testing Requirements
Every tool needs:
1. Happy path test (normal input, expected output)
2. Safety test (if tool touches /cmd_vel or blacklisted services)
3. Edge case test (empty topic list, disconnected rosbridge, malformed message)

```python
# Test naming convention
def test_ros_publish_topic_clamps_velocity_over_limit():
def test_ros_publish_topic_executes_within_limit():
def test_ros_call_service_blocks_without_confirmation():
def test_ros_call_service_executes_with_confirmation():
```

## Dependency Rules
- Add to `requirements.txt` immediately when importing a new package
- Pin major versions: `fastmcp>=2.0,<3.0`
- Never use a package that requires ROS installation to import
  (rosbridge communication goes through WebSocket, not Python ROS bindings)

## Git Hygiene (remind user if they paste messy commits)
- One logical change per commit
- Commit message: `type(scope): description`
  - `feat(tools): add ros_list_topics with message type support`
  - `fix(safety): prevent velocity clamp bypassing via negative values`
  - `test(safety): add adversarial prompt resistance tests`
- Never commit: `logs/`, `__pycache__/`, `.env`
