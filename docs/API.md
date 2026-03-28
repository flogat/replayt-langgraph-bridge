# Public adapter API and module layout

Normative contract for integrators: what may be imported, stability expectations, and how this relates to other specs.

## Goals

- **Small surface** — Prefer factory/builder entry points (`compile_replayt_workflow`, `initial_bridge_state`) and typed shapes over exposing LangGraph wiring details.
- **One import path** — Integrators should use `from replayt_langgraph_bridge import …` (or `import replayt_langgraph_bridge`). Submodules under `replayt_langgraph_bridge` are **not** a second public API unless explicitly listed below as supported.
- **Documented stability** — Every name in the public export set has a docstring (module or object) and is summarized here and in **[README.md](../README.md)**.

## Source of truth for exported names

The package attribute `replayt_langgraph_bridge.__all__` is the **canonical list** of supported public symbols. Maintainers must keep **`src/replayt_langgraph_bridge/__init__.py`** `__all__`, this document, and the **Public API** section of **[README.md](../README.md)** aligned whenever that set changes.

## Stable public symbols (integrator-facing)

These names are **stable** under semantic versioning for this package: breaking changes require a **major** version bump once the project reaches **1.0**; during **0.x**, treat minor releases as able to add symbols or deprecate with warnings, and reserve breaking removals or signature changes for a minor bump with **[CHANGELOG.md](../CHANGELOG.md)** notes (per project practice).

| Symbol | Role |
| ------ | ---- |
| `compile_replayt_workflow` | Build a LangGraph compiled graph from a replayt `Workflow`. |
| `initial_bridge_state` | Construct validated initial channel state for the first `invoke`. |
| `ReplaytBridgeState` | `TypedDict` describing the bridge channel shape (`context`, `replayt_next`, optional `bridge_state_schema_version`). Wire format and limits are normative in **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**. |
| `BridgeStateValidationError` | Raised for rejected inbound state (subclass of `ValueError`; stable, generic `str` messages). |
| `RedactorHook` | Type alias (`Callable[[dict[str, Any]], dict[str, Any]]`) for custom log attachment redaction; behavior in **[LOG_REDACTION.md](LOG_REDACTION.md)**. |
| `get_bridge_logger` | Return the bridge logger used for structured records (`LogRecord.replayt_bridge`). |
| `redact_log_attachment` | Redact a single attachment dict (tests and advanced callers); same rules as **[LOG_REDACTION.md](LOG_REDACTION.md)**. |
| `__version__` | Package version string. |

### Experimental and internal (normative rules)

- **Experimental** APIs, when introduced, must be labeled in their docstring with explicit “experimental” wording (and ideally a version note) **and** called out in **[CHANGELOG.md](../CHANGELOG.md)** under **Unreleased** until promoted to stable (then listed in the table above and in `__all__`).
- **No experimental surface today** — all names in `__all__` are treated as stable under the 0.x policy above.
- **Internal** — Any Python name prefixed with `_`, any module not re-exported through `__all__`, and any object not listed in this document’s stable table are **not supported** for integrators. They may change without notice.

## Submodule layout (maintainers and tests)

These files exist under `src/replayt_langgraph_bridge/`. Integrators should **not** depend on them; documentation and tests may reference them.

| Module | Purpose |
| ------ | ------- |
| `graph.py` | Graph compilation, node wiring, `ReplaytBridgeState` / `ReplaytBridgeContext` runtime typing for LangGraph. `ReplaytBridgeContext` is **not** exported in `__all__`; integrators only need to pass `context={"runner": runner}` as documented on `compile_replayt_workflow`. |
| `state_validation.py` | Inbound payload validation, checkpointer wrapper. |
| `redaction.py` | Default redaction and `RedactorHook` implementation helpers. |
| `bridge_log.py` | Structured log emission helpers. |

In-repo **tests** may import private helpers (e.g. functions prefixed with `_` in `graph.py`) to lock behavior; that is not a license for applications to do the same.

## Cross-spec index

| Topic | Normative doc |
| ----- | ------------- |
| Checkpoint persistence scope, backends pattern (langgraph 1.1.x), failure modes | **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** |
| Hosted checkpoints, remote runtimes, TLS, and access control | **[HOSTED_DEPLOYMENT_AUTHZ.md](HOSTED_DEPLOYMENT_AUTHZ.md)** |
| Inbound state limits and schema version | **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** |
| Bridge-originated logging and redaction | **[LOG_REDACTION.md](LOG_REDACTION.md)** |
| Replayt-facing tests and assertion style | **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** |
| Dependency ranges and compatibility process | **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md#dependency-and-pin-policy)** |

## Builder acceptance checklist (backlog: public API)

Use this to verify the backlog item **Define the public adapter API and module layout** is satisfied in code and docs:

1. **`__all__`** matches the stable table in this section (same names, no accidental drift).
2. Each stable symbol has a **docstring** (or, for `RedactorHook`, a clear module-level description where the alias is defined) describing parameters, returns, and links to the relevant normative doc where appropriate.
3. **[README.md](../README.md)** Public API section and **Usage** example import **only** from `replayt_langgraph_bridge` (not from submodules).
4. This file (**docs/API.md**) stays in sync when the public set changes.
