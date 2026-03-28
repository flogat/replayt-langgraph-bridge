# Design principles

Revise as the project matures. Defaults below are minimal—expand with rules for **your** codebase.

1. **Explicit contracts** — Document supported replayt (and third-party framework) versions; test integration boundaries.
2. **Small public surfaces** — Prefer narrow APIs and documented extension points. The canonical export list, submodule layout, and stability rules for integrators are in **[API.md](API.md)** (`__all__` in `replayt_langgraph_bridge.__init__` must stay aligned with that doc and the README).
3. **Observable automation** — Local scripts and CI produce clear logs and exit codes.
4. **Consumer-side maintenance** — Compatibility shims and pins live **here**; upstream changes are tracked with tests
   and changelog notes.
5. **Not a lever on core** — This repo does not exist to steer replayt core; propose upstream changes through normal
   channels.

## Replayt boundary testing

Integration-style tests that import **replayt** must fail with **messages that name the contract** under test (handler transitions, `RunContext.data`, runner/store wiring, etc.), not only deep stack traces. Normative expectations, anti-patterns, skip/issue rules, and the backlog checklist live in **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)**.

## Dependency and Pin Policy

This section is the **source of truth** for how pins, ranges, and extras are chosen. The README summarizes it for integrators; **`pyproject.toml`** is the machine-readable contract.

### Minimum supported vs upper bounds vs what CI exercises

| Concept | Meaning in this repo | Where it lives |
| -------- | -------------------- | -------------- |
| **Minimum supported** | Lowest **replayt** / **LangGraph** / **Python** versions the maintainers commit to supporting, based on features the bridge uses and security posture | Lower bounds in `[project.dependencies]` and `requires-python`; repeated in this doc for readability |
| **Upper bounds** | `< next major` on **replayt** and **langgraph** so `pip install` does not silently pull a new major | Upper bounds in `[project.dependencies]` |
| **Tested matrix (today)** | **Python** 3.11 and 3.12 in GitHub Actions; each job runs `pip install -e .[dev]` and **pytest**. Runtime packages are whatever **pip** resolves **within** the declared ranges on that run (not a separate per-package pin file) | `.github/workflows/ci.yml` |
| **Core install in CI** | At least one job path must install the bridge for tests **without** optional **demo / LLM-sample** extras (today: `pip install -e ".[dev]"` only). When a **`demo`** (or similarly named) extra exists, CI must still prove the **default + dev** surface is enough for the main test suite. | `.github/workflows/ci.yml`; README **Dependency strategy** |
| **Optional verification** | Before widening ranges or after upstream incidents, maintainers may install explicit versions locally or in a branch (e.g. `pip install 'replayt==x.y.z'`) and run **pytest**; document outcomes in a compatibility issue | Maintainer workflow; see template below |

Optional extras must stay **out of** `[project.dependencies]` unless they are required for the published bridge API at install time.

### Version selection rules

- **Minimum supported versions**: Set from tested bridge behavior and acceptable security posture; do not set a floor higher than necessary without cause.
- **Upper bounds**: Prefer `< next-major` on **replayt** and **langgraph** until CI and release notes prove the next major is safe.
- **Optional extras**: Declare under `[project.optional-dependencies]` only. **`dev`** holds tooling (**pytest**, **ruff**, **pip-audit**); it is not installed for `pip install replayt-langgraph-bridge` without an extra.
- **Demo / LLM provider clients**: Packages needed **only** for examples or integration samples that call **vendor LLM APIs** (OpenAI, Anthropic, etc.) must **not** appear in `[project.dependencies]`. Declare them under a dedicated optional extra (recommended name: **`demo`**, or `llm-demo` if you need to disambiguate). Document in the README extras matrix that installing that extra opts into those clients and the **network / credential** expectations that come with them.

### Core vs demo extras (LLM clients and supply chain)

**Goal:** A default `pip install replayt-langgraph-bridge` (no extras) must not pull in **direct** dependencies whose **primary, documented purpose** is acting as a **vendor LLM HTTP/API client** (for example `openai`, `anthropic`, `langchain-openai`, `langchain-anthropic`—the exact list is maintained in **`pyproject.toml`** comments and reviewed when deps change). Generic libraries already required for the bridge (for example **langgraph** and its transitive stack) are allowed even if they are network-capable; this rule targets **optional demo** and **provider SDK** surface area the bridge does not need at runtime for its public API.

**Normative acceptance criteria (builder checklist):**

1. **Core dependency set** — `[project.dependencies]` lists only what is required to import and run the **documented public bridge API** without optional samples. It does **not** list LLM vendor SDKs or thin wrappers whose reason to exist is calling those APIs.
2. **Demo extra** — Any such SDK (or demo-only stack) appears only under `[project.optional-dependencies]` in an extra named in the README matrix (e.g. **`demo`**), with a short comment per requirement in **`pyproject.toml`**.
3. **README extras matrix** — Table covers: **no extra** (core runtime), **`dev`**, and **`demo`** (when present). Include a column stating whether that install surface is intended to add **outbound LLM vendor** client libraries (core: **no**; **`dev`**: **no**; **`demo`**: **yes** when those deps are present).
4. **CI** — The primary **test** job (or an equivalent documented job) installs **`[dev]`** but **not** **`[demo]`**, and the full suite expected for integrators passes. Tests that require the demo extra must be **skipped** or moved behind a marker when the extra is not installed (document the pattern in **`REPLAYT_BOUNDARY_TESTS.md`** or **`CONTRIBUTING.md`** when introduced).
5. **Contract tests** — Extend **`tests/test_dependency_strategy.py`** (or follow-on tests) so the **denylist** of direct core deps and the **presence** of demo-only packages only under the demo extra are enforced, matching **`pyproject.toml`**.

### Justifying new or changed runtime constraints

When the first integration (or any later change) adds or tightens **runtime** dependencies:

1. Put a short comment next to the requirement in **`pyproject.toml`** (why the bound exists).
2. Update **Current dependency constraints** below and the compatibility bullets in **`README.md`** if integrator-facing ranges change.
3. Add or adjust **`CHANGELOG.md`** under **Unreleased** when the change is user-visible (new runtime dep, range change, or new extra).

### Current dependency constraints

- **replayt**: `>=0.4.0,<0.5` (initial integration target, 0.4.x line)
- **LangGraph** (`langgraph` on PyPI): `>=1.1.0,<1.2` (initial integration target, 1.1.x line)
- **Python**: `>=3.11` (`requires-python`, aligned with supported stack)
- **demo** (optional): **openai**, **anthropic**, **langchain-openai**, **langchain-anthropic** under `[project.optional-dependencies] demo` for vendor-LLM samples only; CI default path does not install this extra (see README extras matrix).

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

- [x] **Policy written** — This section and the README **Dependency strategy** describe pins, ranges, optional extras, and minimum vs CI-tested interpretation consistently.
- [x] **Runtime vs dev** — `[project.dependencies]` lists only what end users need; `[project.optional-dependencies] dev` lists contributor tooling; no dev-only tools in core dependencies.
- [x] **Justified constraints** — Each runtime requirement in **`pyproject.toml`** has a maintainer-facing comment; constraints match **Current dependency constraints** here and **`README.md`** compatibility lines.
- [x] **Breaking upstream path** — Triage uses the compatibility issue template and the maintainer checklist above; **`CONTRIBUTING.md`** points maintainers at this policy and the template for bumps.
- [x] **Core vs demo LLM clients** — **[Core vs demo extras (LLM clients and supply chain)](#core-vs-demo-extras-llm-clients-and-supply-chain)** checklist is satisfied: no LLM vendor SDKs in core `[project.dependencies]`; optional **`demo`** extra and README matrix when demo deps exist; CI tests **without** that extra; contract tests updated (**backlog: Isolate optional LLM demo extras from core bridge install**).

## Security considerations

1. **Trust boundary** — Workflow step handlers, the `Workflow` definition, and the `Runner` (and its store) are
   integrator-controlled. The bridge forwards execution to replayt and LangGraph; it does not sandbox or authenticate
   application logic.
2. **Durable state** — `ReplaytBridgeState["context"]` is shallow-merged across updates and may be written by LangGraph
   checkpointers you supply. Treat checkpoint backends like any persistence layer: do not put secrets or sensitive PII in
   graph state unless your storage and retention policies allow it. Normative scope, supported checkpointer pattern for **langgraph 1.1.x**, in-memory vs durable usage, and failure modes for bad or skewed checkpoint-related data are in **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)**. **Log redaction** (deny-listed keys, value patterns, optional
   integrator hook, strict mode via `REPLAYT_BRIDGE_STRICT_REDACT`) applies to **bridge-originated structured logs** as specified
   in **[LOG_REDACTION.md](LOG_REDACTION.md)**; it is not a substitute for checkpoint access control or integrator-side state hygiene.
3. **Errors and logging** — Transition validation raises `RuntimeError` messages that include step names and allowed
   targets to aid debugging. Avoid logging full graph state in production if it may contain sensitive fields. Bridge-originated
   structured logs follow **[LOG_REDACTION.md](LOG_REDACTION.md)**.
4. **Inbound state validation** — Dict-shaped `ReplaytBridgeState` at the bridge boundary (initial input and
   checkpoint-resumed channel state) is validated as **untrusted** per **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**:
   documented limits and schema versions, generic caller-facing errors, and no partial durable mutation on reject
   (enforced in `replayt_langgraph_bridge.state_validation` and `graph.py`).

For a detailed threat model, see [THREAT_MODEL.md](THREAT_MODEL.md). For checkpoint persistence scope and failure modes, see [CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md). For hosted or networked checkpoint stores and remote graph runtimes (topology table, TLS, IAM-style controls, dev/stage/prod separation, upstream LangGraph/replayt links), see [HOSTED_DEPLOYMENT_AUTHZ.md](HOSTED_DEPLOYMENT_AUTHZ.md). For redaction rules and extension points, see [LOG_REDACTION.md](LOG_REDACTION.md). For inbound payload hardening, see [STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md).

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

## LLM and demos

### Package scope (normative)

- **Core bridge** (`pip install replayt-langgraph-bridge`) and **`[dev]`** tooling: **Out of scope** for outbound calls to **vendor LLM HTTP APIs** as part of this package’s default behavior. The primary CI **`test`** job mirrors that path: **`pip install -e ".[dev]"`** only, **no** **`[demo]`** extra, **no** scripted live model invocations (see **`.github/workflows/ci.yml`**).
- **Optional samples:** **In scope** only as **integrator-opt-in** paths: install **`replayt-langgraph-bridge[demo]`**, supply **environment-backed** API credentials, run samples locally or in your own automation. Packaging rules: **[Core vs demo extras](#core-vs-demo-extras-llm-clients-and-supply-chain)**—vendor LLM clients **never** belong in `[project.dependencies]`.

### Current repository state

| Artifact | Status |
| -------- | ------ |
| **`demo` extra** (**openai**, **anthropic**, **langchain-openai**, **langchain-anthropic**) | Declared in **`pyproject.toml`** for optional vendor-LLM samples |
| Runnable first-party LLM demo / `examples/` in this repo | **Not shipped** — deterministic tests and integrator-owned graphs apply; see **[MISSION.md](MISSION.md#llm-demos-and-optional-samples-scope)** |
| CI default **`test`** job | **`[dev]`** only; no keys or live provider calls required |

### Builder acceptance criteria (LLM demo boundaries)

Use this checklist when validating docs and (later) shipped samples against the backlog **Document LLM boundaries for demos and optional examples**:

1. **Scope statement** — **`docs/MISSION.md`** states whether LLM demos are in scope (same contract as this section: optional **`demo`** path only; core + default CI remain LLM-call-free).
2. **When a runnable first-party demo exists in-repo** — README documents **required environment variables**, **cost** expectations (vendor-metered; the bridge does not enforce quotas), and **log / redaction** policy: bridge logs follow **[LOG_REDACTION.md](LOG_REDACTION.md)**; demo code must follow **[Secrets policy](#secrets-policy)** and avoid logging raw keys or sensitive prompts. CI’s **default** **`test`** job remains **`[dev]`**-only with **no** live model calls. Tests that need the **`demo`** extra use **`importorskip`** / markers per **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)**.
3. **When no runnable demo exists** — README and this section **say so explicitly** and point to the **`demo`** extra, **[MISSION.md](MISSION.md#llm-demos-and-optional-samples-scope)**, and **[REPLAYT_ECOSYSTEM_IDEA.md](REPLAYT_ECOSYSTEM_IDEA.md#optional-vendor-llm-samples)** for future work.

### Packaging and operations (summary)

**Packaging:** Optional samples that depend on **vendor LLM clients** use the **`demo`** extra and the **[Core vs demo extras](#core-vs-demo-extras-llm-clients-and-supply-chain)** rules—not `[project.dependencies]`.

**Secrets and redaction:** Follow **[Secrets policy](#secrets-policy)** and **[LOG_REDACTION.md](LOG_REDACTION.md)** for API keys and logged payloads. **MISSION.md** summarizes operational expectations for integrators.

## Audience (extend)

| Audience | Needs |
| -------- | ----- |
| **Maintainers** | Mission, scripts, pinned versions, release notes |
| **Integrators** | Stable adapter surface, compatibility matrix |
| **Contributors** | README, tests, coding expectations |
