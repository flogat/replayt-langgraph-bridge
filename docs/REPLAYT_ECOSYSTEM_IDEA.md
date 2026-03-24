# Positioning — LangGraph adapter mapping replayt workflow states to graph nodes and checkpoints

This project **uses** [replayt](https://pypi.org/project/replayt/). It is **not** a fork of replayt. Compatibility,
version pins, and CI are maintained **in this repository** (consumer-side), not inside replayt core.

**Test coverage (required):** Ship automated tests for behavior you claim (unit, contract/integration at replayt
boundaries, smoke where useful). Document how to run them in the README and CI.

---

## Primary pattern: framework bridge

**One-line pitch:** Provide a thin, versioned adapter so replayt workflow state and checkpoints map cleanly onto LangGraph
graphs—letting teams use LangGraph as the runtime façade while replayt remains the source of truth for durable workflow
semantics.

**Why this leads:** The main deliverable is interoperability between two ecosystems, not a demo app, not a new combinator
product, and not filling a gap we pretend belongs in replayt core.

**Maintenance stance:**

- **Pins** — Declare supported `replayt` and `langgraph` versions in `pyproject.toml` (and tighten or widen based on CI).
  Treat major/minor bumps in either dependency as explicit adapter work, not silent upgrades.
- **Consumer-side compatibility** — Shims, workarounds, and graph/checkpoint mapping fixes live **here**; we track
  upstream releases with tests and changelog notes. We do not use this repo to steer replayt core (see
  **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)**).

**Public API of the bridge:** The Python package under `src/replayt_langgraph_bridge/` (import `replayt_langgraph_bridge`);
concrete modules and symbols will grow with implementation and stay documented in README or reference docs.

**First supported versions:** The adapter targets **replayt 0.4.x** and **LangGraph 1.1.x** on PyPI; declared ranges live in
**`pyproject.toml`** (`replayt>=0.4.0,<0.5`, `langgraph>=1.1.0,<1.2`) and may widen as CI proves patch compatibility.

---

## Other patterns (context only)

These describe *adjacent* ways a replayt-related repo might be shaped. **This repo’s leading pattern is (3) only.**

### 1) Core-gap

_Use when replayt core intentionally omits a capability._

### 2) LLM showcase

_Concrete demo that needs model calls._ Not the primary goal of this adapter; any LLM usage would be documented under
**[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** / MISSION if added later.

### 3) Framework bridge _(primary)_

_See section above._

### 4) Combinator

_Novel composition of replayt + other tools._ Possible future examples could build on this bridge, but the repo’s mission
remains the LangGraph adapter first.
