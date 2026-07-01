"""CommandLogger: append-only audit log for every Claude-issued tool call.

One line per tool invocation, written to ``logs/commands.log`` (path from safety_config.yaml).
The log is the audit trail for safety events — clamps, blocks, and confirmation gates all leave
a record here. Format follows .claude/rules/safety-layer.md.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).parents[2]
_DEFAULT_CONFIG = _REPO_ROOT / "config" / "safety_config.yaml"
_DEFAULT_LOG_PATH = "logs/commands.log"


def _resolve_config(config_path: str | None) -> Path:
    """Explicit arg wins, else the ROS_SAFETY_CONFIG env override, else the packaged default."""
    if config_path:
        return Path(config_path)
    return Path(os.environ.get("ROS_SAFETY_CONFIG", _DEFAULT_CONFIG))


class CommandLogger:
    """Writes a timestamped audit line for each tool call to the configured log file."""

    def __init__(self, config_path: str | None = None) -> None:
        """Resolve the log path from config; create the parent directory if missing."""
        path = _resolve_config(config_path)
        with open(path, "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh) or {}
        rel = config.get("logging", {}).get("path", _DEFAULT_LOG_PATH)
        log_path = Path(rel)
        self.path = log_path if log_path.is_absolute() else _REPO_ROOT / log_path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, tool: str, args: dict, outcome: str, reason: str = "") -> None:
        """Append one audit line: [ISO-8601] TOOL=.. | ARGS=.. | OUTCOME=.. | REASON=.."""
        timestamp = datetime.now(timezone.utc).isoformat()
        args_json = json.dumps(args, default=str, sort_keys=True)
        line = f"[{timestamp}] TOOL={tool} | ARGS={args_json} | OUTCOME={outcome} | REASON={reason}\n"
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line)


def log_and_return(tool: str, args: dict, result: dict) -> dict:
    """Audit-log a completed tool call and return its result dict unchanged.

    Used at every tool return path so success, error, clamped, and blocked outcomes are all
    recorded. ``outcome`` mirrors the result's ``status`` field.
    """
    CommandLogger().log(
        tool=tool, args=args, outcome=result["status"], reason=result.get("message", "")
    )
    return result
