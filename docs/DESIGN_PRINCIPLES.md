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
