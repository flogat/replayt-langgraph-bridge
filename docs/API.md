# Public adapter API and module layout

Normative contract for integrators: what may be imported, stability expectations, and how this relates to other specs.

## Goals

- **Small surface** — Prefer factory/builder entry points (`compile_replayt_workflow`, `initial_bridge_state`) and typed shapes over exposing LangGraph wiring details.
- **One import path** — Integrators should use `from replayt_langgraph_bridge import …` (or `import replayt_langgraph_bridge`). Submodules under `replayt_langgraph_bridge` are **not** a second public API unless explicitly listed below as supported.
- **Documented stability** — Every name in the public export set has a docstring (module or object) and is summarized here and in **[README.md](../README.md)**.
- **Type checkers** — Public symbols should carry accurate **inline** annotations; whether the distribution ships a PEP 561 **`py.typed`** marker, optional stub policy, and **mypy** / **pyright** smoke (CI or documented commands) are specified in **[BACKLOG_PEP561_TYPING_POSTURE.md](BACKLOG_PEP561_TYPING_POSTURE.md)**.

## Source of truth for exported names

The package attribute `replayt_langgraph_bridge.__all__` is the **canonical list** of supported public symbols. Maintainers must keep **`src/replayt_langgraph_bridge/__init__.py`** `__all__`, this document, and the **Public API** section of **[README.md](../README.md)** aligned whenever that set changes.

## Stable public symbols (integrator-facing)

These names are **stable** under semantic versioning for this package: breaking changes require a **major** version bump once the project reaches **1.0**; during **0.x**, treat minor releases as able to add symbols or deprecate with warnings, and reserve breaking removals or signature changes for a minor bump with **[CHANGELOG.md](../CHANGELOG.md)** notes (per project practice).

| Symbol | Role |
| ------ | ---- |
| `compile_replayt_workflow` | Build a LangGraph compiled graph from a replayt `Workflow`. Compile-time error contract: **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)**. For many steps, see the same doc §5 (non-normative scale and profiling guidance). |
| `initial_bridge_state` | Construct validated initial channel state for the first `invoke`. |
| `ReplaytBridgeState` | `TypedDict` describing the bridge channel shape (`context`, `replayt_next`, optional `bridge_state_schema_version`). Wire format and limits are normative in **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**. |
| `BridgeStateValidationError` | Raised for rejected inbound state (subclass of `ValueError`; stable, generic `str` messages). |
| `BridgeWorkflowCompileError` | Subclass of `ValueError` for compile-time workflow misuse (unset `initial_state` or initial step not registered). See **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)**. |
| `BridgeGraphMappingError` | Base for handler return / routing failures during `invoke` (subclass of `Exception`, not `RuntimeError`). Subclasses set a stable string `code`. |
| `BridgeTransitionError` | Subclass of `BridgeGraphMappingError` with `code == "undeclared_transition"` when a handler return violates declared edges. |
| `BridgeRoutingError` | Subclass of `BridgeGraphMappingError` with `code == "unknown_next"` when `replayt_next` names an unknown step. |
| `BridgeLargeGraphWarning` | Subclass of `UserWarning`; **at most once per interpreter process**, `compile_replayt_workflow` may emit this when the workflow step count reaches the high threshold documented in **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)** §4.3 (non-fatal). Filter with `warnings.filterwarnings`. |
| `RedactorHook` | Type alias (`Callable[[dict[str, Any]], dict[str, Any]]`) for custom log attachment redaction; behavior in **[LOG_REDACTION.md](LOG_REDACTION.md)**. |
| `get_bridge_logger` | Return the bridge logger used for structured records (`LogRecord.replayt_bridge`). |
| `redact_log_attachment` | Redact a single attachment dict (tests and advanced callers); same rules as **[LOG_REDACTION.md](LOG_REDACTION.md)**. |
| `__version__` | Package version string. |

### Bridge logging (silence and verbosity)

The bridge uses the stdlib logger named `replayt_langgraph_bridge` unless you pass `bridge_logger` to `compile_replayt_workflow`. That logger uses level `NOTSET` and `propagate=True`, so the effective threshold follows ancestor loggers (often the root at `WARNING`). **ERROR** records can still reach `stderr` through the interpreter last-resort handler when no handler is configured. **INFO** and **DEBUG** need a handler on this logger or an ancestor, or `logging.basicConfig` (or equivalent) on the root.

Compile-time and routing failures are specified in **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)**; related diagnostics use the same bridge logger. Inbound state validation can log on that logger too; see **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**. Structured attachments follow **[LOG_REDACTION.md](LOG_REDACTION.md)** when `redact=True` (default).

To silence bridge output, attach `logging.NullHandler` to `replayt_langgraph_bridge`, set `propagate=False`, tune levels, or pass a no-op `bridge_logger`.

```python
import logging

log = logging.getLogger("replayt_langgraph_bridge")
log.addHandler(logging.NullHandler())
log.propagate = False
```

### Experimental and internal (normative rules)

- **Experimental** APIs, when introduced, must be labeled in their docstring with explicit “experimental” wording (and ideally a version note) **and** called out in **[CHANGELOG.md](../CHANGELOG.md)** under **Unreleased** until promoted to stable (then listed in the table above and in `__all__`).
- **No experimental surface today** — all names in `__all__` are treated as stable under the 0.x policy above.
- **Internal** — Any Python name prefixed with `_`, any module not re-exported through `__all__`, and any object not listed in this document’s stable table are **not supported** for integrators. They may change without notice.

## Submodule layout (maintainers and tests)

These files exist under `src/replayt_langgraph_bridge/`. Integrators should **not** depend on them; documentation and tests may reference them.

| Module | Purpose |
| ------ | ------- |
| `graph.py` | Graph compilation, node wiring, `ReplaytBridgeState` / `ReplaytBridgeContext` runtime typing for LangGraph. `ReplaytBridgeContext` is **not** exported in `__all__`; integrators only need to pass `context={"runner": runner}` as documented on `compile_replayt_workflow`. |
| `errors.py` | Public exception types for compile and mapping failures (re-exported from the package root). |
| `state_validation.py` | Inbound payload validation, checkpointer wrapper. |
| `redaction.py` | Default redaction and `RedactorHook` implementation helpers. |
| `bridge_log.py` | Structured log emission helpers. |

In-repo **tests** may import private helpers (e.g. functions prefixed with `_` in `graph.py`) to lock behavior; that is not a license for applications to do the same.

## Cross-spec index

| Topic | Normative doc |
| ----- | ------------- |
| Checkpoint persistence scope, backends pattern (langgraph 1.1.x), failure modes | **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** |
| Backlog: checkpoint slice acceptance criteria and in/out of scope | **[BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md](BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md)** |
| Hosted checkpoints, remote runtimes, TLS, and access control | **[HOSTED_DEPLOYMENT_AUTHZ.md](HOSTED_DEPLOYMENT_AUTHZ.md)** |
| Inbound state limits and schema version | **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** |
| Compile-time and routing/mapping errors (`compile_replayt_workflow`, `replayt_next`) | **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)** |
| Large workflows: non-normative scale expectations, profiling pointers, optional advisory spec | **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)** §5–§4.3; **[BACKLOG_LARGE_WORKFLOW_COMPILE_ERGONOMICS.md](BACKLOG_LARGE_WORKFLOW_COMPILE_ERGONOMICS.md)** |
| Bridge logger qualname, default levels, silence | **[Bridge logging](#bridge-logging-silence-and-verbosity)** |
| Bridge-originated logging and redaction | **[LOG_REDACTION.md](LOG_REDACTION.md)** |
| Replayt-facing tests and assertion style | **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** |
| Dependency ranges and compatibility process | **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md#dependency-and-pin-policy)** |
| PEP 561 **`py.typed`**, stub policy, contributor annotation rules | **[BACKLOG_PEP561_TYPING_POSTURE.md](BACKLOG_PEP561_TYPING_POSTURE.md)** |
| Streaming / async LangGraph calls vs bridge-tested **`invoke`** path | **[Streaming and async LangGraph entry points](#streaming-and-async-langgraph-entry-points-invoke-stream-astream)**; backlog spec **[BACKLOG_STREAMING_ASYNC_API_STANCE.md](BACKLOG_STREAMING_ASYNC_API_STANCE.md)** |

## `compile_replayt_workflow` (extra keyword arguments)

Beyond the parameters summarized in **[README.md](../README.md)** (Public API), **`interrupt_before`** and **`interrupt_after`** are passed through to LangGraph **`StateGraph.compile`**. Lists use **replayt `Workflow` step names** (the same strings you pass to `@workflow.step`). Typical use is a non-`None` **checkpointer** plus one or more **`invoke`** calls on the same **`thread_id`**; see **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** §3 and §7.

**Large workflows:** After a successful compile, the bridge may issue **`BridgeLargeGraphWarning`** once per process when the step count is at or above the threshold fixed next to **`_LARGE_GRAPH_STEP_THRESHOLD`** in **`replayt_langgraph_bridge.graph`** (currently **256**). This is non-fatal; see **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)** §4.3 and §5.

**Human-in-the-loop:** copy-paste **`MemorySaver`**, **`thread_id`**, and two-**`invoke`** wiring (**`interrupt_after`** example) live in the **Human-in-the-loop** subsection of **[README.md](../README.md)** (immediately after **Checkpoint-enabled usage**).

## Streaming and async LangGraph entry points (`invoke`, `stream`, `astream`)

**Documented and CI-tested path:** Use synchronous **`CompiledStateGraph.invoke`** with **`initial_bridge_state`**, optional LangGraph **`config`** (e.g. **`thread_id`** when a **`checkpointer`** is set), and **`context={"runner": runner}`**. README examples, checkpoint guidance in **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)**, and **`tests/`** all follow this pattern.

**LangGraph streaming and async APIs:** The object returned by **`compile_replayt_workflow`** is a normal LangGraph **`CompiledStateGraph`**, which also exposes upstream methods such as **`stream`**, **`astream`**, **`ainvoke`**, **`batch`**, and **`abatch`**. Semantics—**`stream_mode`**, **`version="v2"`** chunk shapes, subgraph streaming, checkpoint/task debug streams, and async **`RunnableConfig`** / Python-version caveats—are defined by **LangGraph**, not extended or wrapped by this package. Start with the official guide **[LangGraph streaming (Python)](https://docs.langchain.com/oss/python/langgraph/streaming)** and the **`CompiledStateGraph`** / **`Pregel`** reference for the **langgraph** version you run (declared range in **`pyproject.toml`**). Persistence-oriented behavior when streaming checkpoint-related modes remains subject to **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** and **[HOSTED_DEPLOYMENT_AUTHZ.md](HOSTED_DEPLOYMENT_AUTHZ.md)**.

**What the bridge does not guarantee:** Maintainers do **not** treat **`stream`**, **`astream`**, or other non-**`invoke`** entry points as a separately tested or documented contract. The bridge registers **synchronous** node functions that call replayt step handlers **synchronously**; there is **no** support for **`async def`** replayt step handlers or bridge-specific streaming adapters. Do **not** assume **`stream`/`astream`** timing, ordering, or checkpoint/interrupt interaction matches every **`invoke`** mental model without checking upstream documentation for your graph and LangGraph version. Per-chunk stream payloads are **not** covered by **[LOG_REDACTION.md](LOG_REDACTION.md)** beyond whatever you emit yourself from integrator code.

Testable backlog mapping and spec-gate checklist: **[BACKLOG_STREAMING_ASYNC_API_STANCE.md](BACKLOG_STREAMING_ASYNC_API_STANCE.md)**.

## Builder acceptance checklist (backlog: public API)

Use this to verify the backlog item **Define the public adapter API and module layout** is satisfied in code and docs:

1. **`__all__`** matches the stable table in this section (same names, no accidental drift).
2. Each stable symbol has a **docstring** (or, for `RedactorHook`, a clear module-level description where the alias is defined) describing parameters, returns, and links to the relevant normative doc where appropriate.
3. **[README.md](../README.md)** Public API section and **Usage** example import **only** from `replayt_langgraph_bridge` (not from submodules).
4. This file (**docs/API.md**) stays in sync when the public set changes.
