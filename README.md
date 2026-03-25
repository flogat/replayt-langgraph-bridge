# LangGraph adapter mapping replayt workflow states to graph nodes and checkpoints

## Overview

This project builds on **replayt** as a **LangGraph framework bridge**. Read
**[docs/REPLAYT_ECOSYSTEM_IDEA.md](docs/REPLAYT_ECOSYSTEM_IDEA.md)** for the primary pattern and compatibility stance, then
**[docs/MISSION.md](docs/MISSION.md)** for users, scope, success metrics, and version intent.

## Design principles

**[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** covers **replayt** compatibility, versioning, integrator security
expectations, and (for showcases) **LLM** boundaries.

For a detailed threat model on checkpoint and state data, see **[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)**.

<<<<<<< HEAD
## Compatibility matrix

| Component | Supported versions | Notes |
|-----------|-------------------|-------|
| replayt | 0.4.x | `replayt>=0.4.0,<0.5` in `pyproject.toml` |
| LangGraph | 1.1.x | `langgraph>=1.1.0,<1.2` in `pyproject.toml` |
| Python | 3.11+ | `requires-python = ">=3.11"` in `pyproject.toml` |

**Version policy:**
- Patch versions within the supported minor version range are automatically compatible
- Minor version bumps require explicit testing and may require bridge updates
- Major version bumps are breaking changes and will require significant bridge updates
=======
## Dependency Strategy

This project follows a deliberate dependency and pin policy to ensure stability for downstream teams:

- **Runtime dependencies**: `replayt>=0.4.0,<0.5` and `langgraph>=1.1.0,<1.2`
- **Version selection**: Minimum supported versions based on tested functionality; upper bounds prevent automatic breaking changes
- **Testing matrix**: CI runs against specific versions to ensure compatibility
- **Breaking changes**: Process established for monitoring, testing, and documenting upstream releases

See **[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** for the complete dependency policy.
>>>>>>> mc/backlog-befc42a4

## Reference documentation (optional)

This checkout does not yet include [`docs/reference-documentation/`](docs/reference-documentation/). You can add markdown
copies of upstream replayt documentation there for offline review or agent context.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
```

## Run tests

```bash
pytest
```

Uses the **dev** extra (`pytest` is listed in `pyproject.toml`). **CI** (GitHub Actions workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml), job **`test`**) runs the same **`pytest`** suite on Python **3.11** and **3.12**.

## Optional agent workflows

This repo may include a [`.cursor/skills/`](.cursor/skills/) directory for Cursor-style agent skills. **`.gitignore`**
lists **`.cursor/skills/`** so those files stay local and are not pushed. Adapt or remove the directory to match your
team's tooling.

## Project layout

| Path | Purpose |
| ---- | ------- |
| `docs/REPLAYT_ECOSYSTEM_IDEA.md` | Positioning; **primary pattern: framework bridge** |
| `docs/MISSION.md` | Mission and scope |
| `docs/DESIGN_PRINCIPLES.md` | Design and integration principles |
| `docs/THREAT_MODEL.md` | Threat model for checkpoint and state data |
| `docs/reference-documentation/` | Optional markdown snapshot for contributors (when present) |
| `src/replayt_langgraph_bridge/` | Python package (`compile_replayt_workflow`, `ReplaytBridgeState`, …) |
| `tests/` | Pytest suite (mirrors CI job **`test`**) |
| `pyproject.toml` | Package metadata and **replayt** / **LangGraph** version ranges |
| `.gitignore` | Ignores `.orchestrator/` and `.cursor/skills/` (local tooling) |
