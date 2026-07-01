"""SafetyMiddleware: velocity clamping and workspace-bounds enforcement.

The middleware is composable — ``apply(topic, message)`` returns a ``(safe_message, SafetyEvent)``
pair and never raises, so callers slot it in at a single call site (see
.claude/rules/safety-layer.md). Config is read from ``config/safety_config.yaml`` on every
instantiation; instantiating fresh per publish therefore picks up live config edits. The one
extra file read per publish is negligible at human interaction rates.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# config/safety_config.yaml relative to this file (mcp/safety/middleware.py -> repo root).
_DEFAULT_CONFIG = Path(__file__).parents[2] / "config" / "safety_config.yaml"


def _resolve_config(config_path: str | None) -> Path:
    """Explicit arg wins, else the ROS_SAFETY_CONFIG env override, else the packaged default."""
    if config_path:
        return Path(config_path)
    return Path(os.environ.get("ROS_SAFETY_CONFIG", _DEFAULT_CONFIG))


@dataclass
class SafetyEvent:
    """Outcome of a safety check on an outbound publish."""

    outcome: str  # one of: success | clamped | blocked | error
    reason: str
    applied: bool


def _clamp(value: float, low: float, high: float) -> float:
    """Clamp ``value`` into the inclusive ``[low, high]`` range."""
    return max(low, min(high, value))


class SafetyMiddleware:
    """Enforces velocity limits and workspace bounds from safety_config.yaml."""

    def __init__(self, config_path: str | None = None) -> None:
        """Load safety config from YAML (default: config/safety_config.yaml)."""
        path = _resolve_config(config_path)
        with open(path, "r", encoding="utf-8") as fh:
            self.config: dict = yaml.safe_load(fh) or {}

    def apply(self, topic: str, message: dict) -> tuple[dict, SafetyEvent]:
        """Return (safe_message, SafetyEvent) for a publish; never raises."""
        if topic.rstrip("/").endswith("cmd_vel"):
            return self._clamp_velocity(message)
        return self._check_bounds(topic, message)

    def _clamp_velocity(self, message: dict) -> tuple[dict, SafetyEvent]:
        """Clamp linear.x and angular.z to configured limits. Always applied on cmd_vel."""
        limits = self.config.get("velocity_limits", {})
        safe = {k: dict(v) if isinstance(v, dict) else v for k, v in message.items()}
        changes: list[str] = []
        for axis_key, field, comp in (("linear_x", "linear", "x"), ("angular_z", "angular", "z")):
            comp_map = safe.get(field)
            if not isinstance(comp_map, dict) or comp not in comp_map:
                continue
            axis = limits.get(axis_key, {})
            low, high = axis.get("min", float("-inf")), axis.get("max", float("inf"))
            original = comp_map[comp]
            clamped = _clamp(original, low, high)
            if clamped != original:
                comp_map[comp] = clamped
                limit = high if original > high else low
                changes.append(f"{field}.{comp} {original} → {clamped} (config limit: {limit})")
        if changes:
            return safe, SafetyEvent("clamped", "Velocity clamped: " + "; ".join(changes), True)
        return safe, SafetyEvent("success", "Within velocity limits; published unchanged.", True)

    def _check_bounds(self, topic: str, message: dict) -> tuple[dict, SafetyEvent]:
        """Reject position-carrying publishes outside workspace bounds (dormant for cmd_vel demo)."""
        position = self._extract_position(message)
        if position is None:
            reason = f"Published to {topic} (no position/velocity constraints apply)."
            return message, SafetyEvent("success", reason, False)
        bounds = self.config.get("workspace_bounds", {})
        for coord, value in position.items():
            lo, hi = bounds.get(coord, [float("-inf"), float("inf")])
            if not lo <= value <= hi:
                reason = (
                    f"Publish blocked: {coord}={value} outside workspace bounds "
                    f"[{lo}, {hi}] (config limit)."
                )
                return message, SafetyEvent("blocked", reason, True)
        return message, SafetyEvent("success", f"Position within workspace bounds on {topic}.", True)

    @staticmethod
    def _extract_position(message: dict) -> dict | None:
        """Pull an {x, y} position from common message shapes, else None."""
        candidate = message.get("position")
        if not isinstance(candidate, dict):
            pose = message.get("pose")
            candidate = pose.get("position") if isinstance(pose, dict) else None
        if not isinstance(candidate, dict):
            return None
        coords = {c: candidate[c] for c in ("x", "y") if c in candidate}
        return coords or None
