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
   graph state unless your storage and retention policies allow it. Automatic shallow redaction (deny-list fields, value masking)
   applied before persistence/logging via built-in `redactor` (opt-in strict mode via `REPLAYT_BRIDGE_STRICT_REDACT=1` env var).
3. **Errors and logging** — Transition validation raises `RuntimeError` messages that include step names and allowed
   targets to aid debugging. Avoid logging full graph state in production if it may contain sensitive fields. Bridge logs use redacted state.

For a detailed threat model, see [THREAT_MODEL.md](THREAT_MODEL.md). For redaction rules and extension points, see [LOG_REDACTION.md](LOG_REDACTION.md).

## Secrets policy

### Environment-backed configuration
- **Preferred method**: Store API keys, tokens, and other secrets in environment variables.
- **Example**: Set `OPENAI_API_KEY`, `LANGCHAIN_API_KEY`, etc., in your shell or deployment environment.
- **Never commit secrets**: Do not commit `.env` files or any files containing raw secrets to version control.

### Secret handling patterns
- **Safe pattern**: Read secrets from environment variables at runtime:
  ```python
  import os
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key:
      raise ValueError("OPENAI_API_KEY environment variable not set")
  ```
- **Anti-pattern**: Hardcoding secrets in code, configuration files, or graph state.
- **Anti-pattern**: Logging raw secrets or including them in error messages.

### LLM and tool integrations
- **LLM providers**: Use environment variables for API keys (OpenAI, Anthropic, etc.).
- **Tool integrations**: Each tool should document its own secret requirements and follow the same pattern.
- **Tracing and exporters**: If using LangSmith or similar exporters, ensure secrets are not logged or stored in traces.

### Demo vs production
- **Demos**: May use environment files for convenience, but never commit them.
- **Production**: Use secure secret management systems (e.g., AWS Secrets Manager, HashiCorp Vault, Kubernetes secrets).
- **Consistency**: The same secret handling patterns should apply to both demo and production paths.

### Rotation
- **Recommended cadence**: Rotate API keys and tokens every 90 days (or per organizational policy) and immediately upon suspected compromise.
- **Automation**: Leverage secret management services with built-in rotation features (e.g., AWS Secrets Manager, Google Secret Manager, HashiCorp Vault).
- **Coordination**: Rotate secrets across all consumers (demos, staging, production) atomically to prevent desynchronization.

### References
- See [THREAT_MODEL.md](THREAT_MODEL.md) for detailed security considerations.
- See [MISSION.md](MISSION.md) for operational guidelines.

## LLM / demos (if applicable)
Document models, secrets handling, cost and redaction expectations here or in MISSION.

## Audience (extend)

| Audience | Needs |
| -------- | ----- |
| **Maintainers** | Mission, scripts, pinned versions, release notes |
| **Integrators** | Stable adapter surface, compatibility matrix |
| **Contributors** | README, tests, coding expectations |
