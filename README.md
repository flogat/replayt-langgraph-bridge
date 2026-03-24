# LangGraph adapter mapping replayt workflow states to graph nodes and checkpoints

## Overview

This project builds on **[replayt](https://pypi.org/project/replayt/)** as a **LangGraph framework bridge**. Read
**[docs/REPLAYT_ECOSYSTEM_IDEA.md](docs/REPLAYT_ECOSYSTEM_IDEA.md)** for the primary pattern and compatibility stance, then
**[docs/MISSION.md](docs/MISSION.md)** for users, scope, success metrics, and version intent.

## Design principles

**[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** covers **replayt** compatibility, versioning, and (for showcases)
**LLM** boundaries.


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
team’s tooling.

## Project layout

| Path | Purpose |
| ---- | ------- |
| `docs/REPLAYT_ECOSYSTEM_IDEA.md` | Positioning; **primary pattern: framework bridge** |
| `docs/MISSION.md` | Mission and scope |
| `docs/DESIGN_PRINCIPLES.md` | Design and integration principles |
| `docs/reference-documentation/` | Optional markdown snapshot for contributors (when present) |
| `src/replayt_langgraph_bridge/` | Python package (`compile_replayt_workflow`, `ReplaytBridgeState`, …) |
| `tests/` | Pytest suite (mirrors CI job **`test`**) |
| `pyproject.toml` | Package metadata and **replayt** / **LangGraph** version ranges |
| `.gitignore` | Ignores `.orchestrator/` and `.cursor/skills/` (local tooling) |
