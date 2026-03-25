# Design principles

Revise as the project matures. Defaults below are minimal—expand with rules for **your** codebase.

1. **Explicit contracts** — Document supported replayt (and third-party framework) versions; test integration boundaries.
2. **Small public surfaces** — Prefer narrow APIs and documented extension points.
3. **Observable automation** — Local scripts and CI produce clear logs and exit codes.
4. **Consumer-side maintenance** — Compatibility shims and pins live **here**; upstream changes are tracked with tests
   and changelog notes.
5. **Not a lever on core** — This repo does not exist to steer replayt core; propose upstream changes through normal
   channels.

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

## Security considerations

1. **Trust boundary** — Workflow step handlers, the `Workflow` definition, and the `Runner` (and its store) are
   integrator-controlled. The bridge forwards execution to replayt and LangGraph; it does not sandbox or authenticate
   application logic.
2. **Durable state** — `ReplaytBridgeState["context"]` is shallow-merged across updates and may be written by LangGraph
   checkpointers you supply. Treat checkpoint backends like any persistence layer: do not put secrets or sensitive PII in
   graph state unless your storage and retention policies allow it.
3. **Errors and logging** — Transition validation raises `RuntimeError` messages that include step names and allowed
   targets to aid debugging. Avoid logging full graph state in production if it may contain sensitive fields.

For a detailed threat model, see [THREAT_MODEL.md](THREAT_MODEL.md).

## Audience (extend)

| Audience | Needs |
| -------- | ----- |
| **Maintainers** | Mission, scripts, pinned versions, release notes |
| **Integrators** | Stable adapter surface, compatibility matrix |
| **Contributors** | README, tests, coding expectations |
