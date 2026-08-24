#!/usr/bin/env bash
#
# install.sh — ros-llm-toolkit cross-machine installer (Month 1)
#
# Installs the TOOLKIT's Python dependencies into a repo-local .venv and generates a
# .mcp.json with absolute paths for Claude Code. It does NOT install ROS 2, Gazebo, or
# TurtleBot3 — those are user prerequisites (see README.md).
#
# Supported: Ubuntu + ROS 2 Humble or Jazzy. Linux-only (requires bash >= 4.0).
# Idempotent: safe to run more than once.

set -euo pipefail

# --- colour helpers (disabled when not a tty or NO_COLOR is set) --------------------
if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
    RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[0;33m'; RESET=$'\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; RESET=''
fi

info()  { printf '%s%s%s\n' "$GREEN"  "$1" "$RESET"; }
warn()  { printf '%s%s%s\n' "$YELLOW" "$1" "$RESET"; }
error() { printf '%s%s%s\n' "$RED"    "$1" "$RESET" >&2; }

# --- bash >= 4.0 guard (macOS ships bash 3; this toolkit is Linux-only) -------------
if (( BASH_VERSINFO[0] < 4 )); then
    error "This installer needs bash >= 4.0 (found ${BASH_VERSION})."
    error "macOS ships bash 3 — ros-llm-toolkit is Linux-only. Run this on Ubuntu."
    exit 1
fi

# --- resolve repo root (never relative, never hardcoded) ----------------------------
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

info "==> ros-llm-toolkit installer"
printf '    Repo root: %s\n' "$REPO_ROOT"

# --- detect ROS 2 distro ------------------------------------------------------------
# Prefer $ROS_DISTRO; fall back to scanning /opt/ros for a single install.
ROS_DISTRO_DETECTED="${ROS_DISTRO:-}"

if [[ -z "$ROS_DISTRO_DETECTED" ]]; then
    if [[ -d /opt/ros ]]; then
        mapfile -t _ros_dirs < <(find /opt/ros -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | sort)
        if (( ${#_ros_dirs[@]} == 1 )); then
            ROS_DISTRO_DETECTED="${_ros_dirs[0]}"
        elif (( ${#_ros_dirs[@]} == 0 )); then
            error "No ROS 2 installation found: \$ROS_DISTRO is unset and /opt/ros is empty."
            error "Install ROS 2 Humble or Jazzy first (see README.md), then re-run."
            exit 1
        else
            error "Multiple ROS 2 distros found under /opt/ros: ${_ros_dirs[*]}"
            error "Ambiguous — set the one to use explicitly, e.g.:  export ROS_DISTRO=humble"
            exit 1
        fi
    else
        error "No ROS 2 installation found: \$ROS_DISTRO is unset and /opt/ros does not exist."
        error "Install ROS 2 Humble or Jazzy first (see README.md), then re-run."
        exit 1
    fi
fi

case "$ROS_DISTRO_DETECTED" in
    humble|jazzy)
        info "==> Detected ROS distro: ${ROS_DISTRO_DETECTED}"
        ;;
    *)
        error "Unsupported ROS distro: '${ROS_DISTRO_DETECTED}'."
        error "ros-llm-toolkit Month 1 supports only: humble, jazzy."
        exit 1
        ;;
esac

# --- create the virtualenv (idempotent) ---------------------------------------------
VENV_DIR="$REPO_ROOT/.venv"
if [[ -d "$VENV_DIR" ]]; then
    info "==> Reusing existing virtualenv: $VENV_DIR"
else
    info "==> Creating virtualenv: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

VENV_PY="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# --- install toolkit dependencies (from pinned requirements.txt) --------------------
REQUIREMENTS="$REPO_ROOT/requirements.txt"
if [[ ! -f "$REQUIREMENTS" ]]; then
    error "requirements.txt not found at $REQUIREMENTS — is the repo intact?"
    exit 1
fi

info "==> Installing Python dependencies into .venv"
"$VENV_PIP" install --upgrade pip >/dev/null
"$VENV_PIP" install -r "$REQUIREMENTS"

# --- validate rosbridge is installed for the detected distro ------------------------
ROSBRIDGE_PKG="ros-${ROS_DISTRO_DETECTED}-rosbridge-suite"
if dpkg -l "$ROSBRIDGE_PKG" 2>/dev/null | grep -q '^ii'; then
    info "==> rosbridge found: $ROSBRIDGE_PKG"
else
    error "Missing required package: $ROSBRIDGE_PKG"
    warn  "Install it, then re-run this script:"
    warn  "    sudo apt update && sudo apt install $ROSBRIDGE_PKG"
    exit 1
fi

# --- generate .mcp.json with absolute paths (idempotent overwrite) ------------------
MCP_JSON="$REPO_ROOT/.mcp.json"
info "==> Writing $MCP_JSON"
cat > "$MCP_JSON" <<EOF
{
  "mcpServers": {
    "ros-llm-toolkit": {
      "type": "stdio",
      "command": "$VENV_PY",
      "args": ["$REPO_ROOT/mcp/server.py"]
    }
  }
}
EOF

# --- done ---------------------------------------------------------------------------
echo
info "Setup complete. Start the stack in three terminals:"
cat <<EOF

  1. rosbridge:
       ros2 launch rosbridge_server rosbridge_websocket_launch.xml

  2. Gazebo + TurtleBot3:
       export TURTLEBOT3_MODEL=burger
       ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

  3. MCP server:
       $VENV_PY $REPO_ROOT/mcp/server.py

Then open Claude Code in this directory — it will pick up .mcp.json automatically.
EOF
