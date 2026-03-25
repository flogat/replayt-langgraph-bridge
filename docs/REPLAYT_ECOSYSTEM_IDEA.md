# replayt-langgraph-bridge in the Replayt Ecosystem

This package **uses** replayt as a dependency. It is **not** a fork or extension of replayt core. Compatibility, version pins, and CI are maintained **in this repository** (consumer-side), not inside replayt core.

## Primary Pattern: Framework Bridge

**One-line pitch:** Thin, versioned adapter so replayt workflow state and checkpoints map cleanly onto LangGraph graphs—letting teams use LangGraph as the runtime façade while replayt remains the source of truth for durable workflow semantics.

**Maintenance Stance:**
- **Pins** — Declare supported `replayt` and `langgraph` versions in `pyproject.toml` (and tighten or widen based on CI). Treat major/minor bumps in either dependency as explicit adapter work, not silent upgrades.
- **Consumer-side compatibility** — Shims, workarounds, and graph/checkpoint mapping fixes live **here**; track upstream releases with tests and changelog notes (see **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)**).

**Public API:** The Python package under `src/replayt_langgraph_bridge/` (import `replayt_langgraph_bridge`).

**First Supported Versions:** Targets **replayt 0.4.x** and **LangGraph 1.1.x** (`replayt>=0.4.0,<0.5`, `langgraph>=1.1.0,<1.2` in `pyproject.toml`); ranges may widen as CI proves patch compatibility.

See **[MISSION.md](MISSION.md)** for users, owned scope vs. delegated responsibilities, and success metrics (including automated tests and CI).
