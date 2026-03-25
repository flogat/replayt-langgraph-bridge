# Design principles

Revise as the project matures. Defaults below are minimal—expand with rules for **your** codebase.

1. **Explicit contracts** — Document supported replayt (and third-party framework) versions; test integration boundaries.
2. **Small public surfaces** — Prefer narrow APIs and documented extension points.
3. **Observable automation** — Local scripts and CI produce clear logs and exit codes.
4. **Consumer-side maintenance** — Compatibility shims and pins live **here**; upstream changes are tracked with tests
   and changelog notes.
5. **Not a lever on core** — This repo does not exist to steer replayt core; propose upstream changes through normal
   channels.

## Dependency and Pin Policy

### Version Selection Strategy
- **Minimum supported versions**: Set based on tested functionality and security patches
- **Upper bounds**: Use `< next-major` to prevent breaking changes from automatic updates
- **Tested matrix**: CI runs against specific versions to ensure compatibility
- **Optional extras**: Clearly separated from core runtime dependencies

### Current Dependency Constraints
- **replayt**: `>=0.4.0,<0.5` (initial integration target, tested with 0.4.x series)
- **LangGraph**: `>=1.1.0,<1.2` (initial integration target, tested with 1.1.x series)
- **Python**: `>=3.11` (matches LangGraph and replayt requirements)

### Breaking Upstream Releases
1. **Monitor**: Watch for new major versions of replayt and LangGraph
2. **Test**: Run existing test suite against new versions
3. **Assess**: Determine if changes affect bridge functionality
4. **Document**: Update compatibility matrix and changelog
5. **Communicate**: Use issue templates to track compatibility work

#### Issue Templates and Maintainer Checklist
- **Issue Template**: Create a "Compatibility Update" issue template in `.github/ISSUE_TEMPLATE/` that includes:
  - Upstream package and version
  - Test results against new version
  - Impact assessment on bridge functionality
  - Required changes (if any)
  - Documentation updates needed
- **Maintainer Checklist**: When a new major version of replayt or LangGraph is released:
  1. Create a new issue using the compatibility template
  2. Run CI against the new version
  3. Document findings in the issue
  4. Update dependency constraints if needed
  5. Release a new version of the bridge with updated constraints

### Rollout Risk for LangGraph Majors
- **Minor/patch updates**: Generally safe, CI should catch regressions
- **Major updates**: Require explicit testing and may need bridge modifications
- **Transition period**: Support both old and new majors during migration if feasible

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
