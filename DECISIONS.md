# Architecture Decision Log
> Log every significant technical decision here with date and reason.
> Never silently change a decision — update this file first.

---

## ADR-001 — ROS 2 Only (No ROS 1)
**Date:** June 2026
**Decision:** Target ROS 2 exclusively. No ROS 1 compatibility layer.
**Reason:** ROS 1 EOL is 2025. Supporting both adds complexity for zero research return.
**Consequence:** Users on ROS 1 cannot use this toolkit. Acceptable tradeoff.
**Status:** Locked

---

## ADR-002 — Month 1 Transport: rosbridge WebSocket
**Date:** June 2026
**Decision:** Use rosbridge WebSocket for Month 1 MCP server.
**Reason:** Faster to POC. Avoids asyncio + rclpy spin threading conflict in early development.
**Consequence:** Higher latency than rclpy native. Acceptable for proof of concept.
**Revisit:** Month 2 — rewrite core transport to rclpy native.
**Status:** Locked for Month 1

---

## ADR-003 — Month 2+ Transport: rclpy Native
**Date:** June 2026
**Decision:** Rewrite MCP server transport to rclpy in Month 2.
**Reason:** Lower latency, better threading control, required for safety layer precision.
**Consequence:** Breaking change from Month 1. Version bump to 0.2.0.
**Status:** Planned

---

## ADR-004 — MCP Framework: FastMCP (Python)
**Date:** June 2026
**Decision:** Use FastMCP as the Python MCP server framework.
**Reason:** Cleanest Python MCP implementation. Active maintenance. Good Claude Desktop compatibility.
**Alternatives considered:** Raw MCP SDK (too verbose), TypeScript MCP (wrong ecosystem for ROS)
**Status:** Locked

---

## ADR-005 — Safety Config Format: YAML
**Date:** June 2026
**Decision:** Safety constraints defined in YAML config file.
**Reason:** Human-readable, easy for engineers to modify without Python knowledge, standard in ROS ecosystem.
**Alternatives considered:** JSON (less readable), Python config (too flexible, security risk)
**Status:** Locked

---

## ADR-006 — Primary Simulation: Gazebo + TurtleBot3
**Date:** June 2026
**Decision:** All development and demo work targets TurtleBot3 in Gazebo.
**Reason:** Widely available, reproducible across machines, standard in ROS 2 tutorials.
**Consequence:** Demo requires TurtleBot3 packages installed. Documented in README.
**Status:** Locked

---

## ADR-007 — Primary Distros: Humble + Jazzy
**Date:** June 2026
**Decision:** Test and support ROS 2 Humble (LTS) and Jazzy (LTS).
**Reason:** Both are Long Term Support releases. Humble widely deployed, Jazzy current.
**Iron support:** Community contribution welcome but not first-party maintained.
**Status:** Locked

---

## ADR-008 — MCP Client: Claude Code (not Claude Desktop)
**Date:** June 2026
**Decision:** Use Claude Code as the Month 1 MCP integration client instead of Claude Desktop.
**Reason:** Anthropic does not ship an official Claude Desktop build for Linux. Claude Code is
the officially supported Linux path, has full MCP support, and is already the development tool
in use — no new install, no extra RAM pressure on an 8GB demo machine.
**Alternatives considered:** Unofficial Linux Desktop build (third-party, unsigned, unnecessary
risk); requiring a second Mac/Windows machine for the demo (adds complexity and failure points).
**Consequence:** MASTER_BRIEF.md's "Claude integration" row needs updating — Claude Code is now
both the Month 1 and Month 3+ client. Demo proof strategy unaffected — same tool-call visibility.
**Status:** Locked

---

## [TEMPLATE — copy for new decisions]
## ADR-00X — [Title]
**Date:**
**Decision:**
**Reason:**
**Alternatives considered:**
**Consequence:**
**Status:** [Locked | Planned | Proposed | Superseded by ADR-00Y]
