"""Safety layer for ros-llm-toolkit.

Velocity clamping + workspace bounds (middleware), command audit log (logger), and the
confirmation gate for blacklisted services (gate). This is the project's novel contribution;
see .claude/rules/safety-layer.md. The layer is always evaluated on the paths it guards and
cannot be bypassed through prompting.
"""
