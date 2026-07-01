"""ConfirmationGate: blocks blacklisted service calls until explicitly confirmed.

Services listed under ``confirmation_required`` in safety_config.yaml (e.g. emergency stop)
cannot be called without a deliberate ``confirm=True``. ``check`` raises ``ConfirmationRequired``;
the calling tool catches it and returns a ``blocked`` result so the MCP contract (always a dict)
holds. See .claude/rules/safety-layer.md.
"""

import logging
import os
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = Path(__file__).parents[2] / "config" / "safety_config.yaml"


def _resolve_config(config_path: str | None) -> Path:
    """Explicit arg wins, else the ROS_SAFETY_CONFIG env override, else the packaged default."""
    if config_path:
        return Path(config_path)
    return Path(os.environ.get("ROS_SAFETY_CONFIG", _DEFAULT_CONFIG))


class ConfirmationRequired(Exception):
    """Raised when a confirmation-required service is called without confirm=True."""

    def __init__(self, service: str) -> None:
        self.service = service
        super().__init__(
            f"'{service}' requires confirmation. Call again with confirm=True to proceed."
        )


class ConfirmationGate:
    """Guards service calls listed under confirmation_required in the safety config."""

    def __init__(self, config_path: str | None = None) -> None:
        """Load the confirmation_required service list from YAML."""
        path = _resolve_config(config_path)
        with open(path, "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh) or {}
        self.required: list[str] = list(config.get("confirmation_required", []))

    def check(self, service: str) -> None:
        """Raise ConfirmationRequired if the service needs confirmation; else return None."""
        if service in self.required:
            raise ConfirmationRequired(service)
