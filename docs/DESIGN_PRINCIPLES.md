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

This section is the **source of truth** for how pins, ranges, and extras are chosen. The README summarizes it for integrators; **`pyproject.toml`** is the machine-readable contract.

### Minimum supported vs upper bounds vs what CI exercises

| Concept | Meaning in this repo | Where it lives |
| -------- | -------------------- | -------------- |
| **Minimum supported** | Lowest **replayt** / **LangGraph** / **Python** versions the maintainers commit to supporting, based on features the bridge uses and security posture | Lower bounds in `[project.dependencies]` and `requires-python`; repeated in this doc for readability |
| **Upper bounds** | `< next major` on **replayt** and **langgraph** so `pip install` does not silently pull a new major | Upper bounds in `[project.dependencies]` |
| **Tested matrix (today)** | **Python** 3.11 and 3.12 in GitHub Actions; each job runs `pip install -e .[dev]` and **pytest**. Runtime packages are whatever **pip** resolves **within** the declared ranges on that run (not a separate per-package pin file) | `.github/workflows/ci.yml` |
| **Optional verification** | Before widening ranges or after upstream incidents, maintainers may install explicit versions locally or in a branch (e.g. `pip install 'replayt==x.y.z'`) and run **pytest**; document outcomes in a compatibility issue | Maintainer workflow; see template below |

Optional extras must stay **out of** `[project.dependencies]` unless they are required for the published bridge API at install time.

### Version selection rules

- **Minimum supported versions**: Set from tested bridge behavior and acceptable security posture; do not set a floor higher than necessary without cause.
- **Upper bounds**: Prefer `< next-major` on **replayt** and **langgraph** until CI and release notes prove the next major is safe.
- **Optional extras**: Declare under `[project.optional-dependencies]` only. **`dev`** holds tooling (**pytest**, **ruff**, **pip-audit**); it is not installed for `pip install replayt-langgraph-bridge` without an extra.

### Justifying new or changed runtime constraints

When the first integration (or any later change) adds or tightens **runtime** dependencies:

1. Put a short comment next to the requirement in **`pyproject.toml`** (why the bound exists).
2. Update **Current dependency constraints** below and the compatibility bullets in **`README.md`** if integrator-facing ranges change.
3. Add or adjust **`CHANGELOG.md`** under **Unreleased** when the change is user-visible (new runtime dep, range change, or new extra).

### Current dependency constraints

- **replayt**: `>=0.4.0,<0.5` (initial integration target, 0.4.x line)
- **LangGraph** (`langgraph` on PyPI): `>=1.1.0,<1.2` (initial integration target, 1.1.x line)
- **Python**: `>=3.11` (`requires-python`, aligned with supported stack)

### Breaking upstream releases — triage

1. **Monitor** — Watch for new **major** (or behavior-changing) releases of **replayt** and **langgraph**.
2. **Track** — Open a **Compatibility Update** issue using **[`.github/ISSUE_TEMPLATE/compatibility_update.md`](../.github/ISSUE_TEMPLATE/compatibility_update.md)** (fields: upstream package/version, test results, impact, required doc and constraint updates).
3. **Test** — Run **pytest** (and supply-chain audit if deps change) against the candidate versions; record pass/fail and surprises in the issue.
4. **Assess** — Decide whether the bridge needs code shims, range-only updates, or a new bridge major.
5. **Document** — Update **`pyproject.toml`**, this section, **`README.md`**, and **`CHANGELOG.md`**; release notes call out compatibility boundary changes.

#### Maintainer checklist (majors and risky bumps)

When **replayt** or **langgraph** ships a new **major**, or you intend to widen/narrow their ranges:

1. File an issue from the compatibility template (link above).
2. Run the test suite against the target versions (local or CI on a branch).
3. Paste or link results in the issue; note any failing tests or API drift.
4. Land constraint and code changes in one coherent change set when possible.
5. Cut a bridge release whose version and changelog reflect the new compatibility story.

### Rollout risk for LangGraph majors

- **Minor/patch** (within the declared range): Expected to be safe; CI on **Python** 3.11/3.12 exercises **latest resolvable** patch releases in range over time.
- **Major** (e.g. 1.2+, 2.x): Assume **breaking** LangGraph API or semantics until proven otherwise; expect bridge changes, expanded tests, and a deliberate range bump—not a silent widen.
- **Transition**: If feasible, support overlapping bridge releases or documented migration steps rather than leaving integrators on an unpinned cliff.

### Builder-facing acceptance criteria (dependency policy backlog)

Treat the following as **done** when the dependency story matches docs and packaging:

- [ ] **Policy written** — This section and the README **Dependency strategy** describe pins, ranges, optional extras, and minimum vs CI-tested interpretation consistently.
- [ ] **Runtime vs dev** — `[project.dependencies]` lists only what end users need; `[project.optional-dependencies] dev` lists contributor tooling; no dev-only tools in core dependencies.
- [ ] **Justified constraints** — Each runtime requirement in **`pyproject.toml`** has a maintainer-facing comment; constraints match **Current dependency constraints** here and **`README.md`** compatibility lines.
- [ ] **Breaking upstream path** — Triage uses the compatibility issue template and the maintainer checklist above; **`CONTRIBUTING.md`** points maintainers at this policy and the template for bumps.

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
