# Graph construction and mapping errors (normative)

This document specifies **bridge-owned** error behavior and observability when a replayt `Workflow` is **compiled** into a LangGraph graph and when **routing** (`replayt_next`) is interpreted during `invoke`. It implements the product backlog **Harden error surfaces and observability for graph construction** so Builders and Testers share one checklist.

**Non-goals:** Errors raised **inside** integrator step handlers (replayt-owned), **LangGraph** internals (except where the bridge calls `compile` and must document propagation), and **inbound channel state** validation — the latter remain in **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** (`BridgeStateValidationError`).

**Related:** **[LOG_REDACTION.md](LOG_REDACTION.md)** (structured logs), **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** (resume vs routing failures), **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** (assertion style for graph tests). **Large graphs (ergonomics, optional warnings):** **[BACKLOG_LARGE_WORKFLOW_COMPILE_ERGONOMICS.md](BACKLOG_LARGE_WORKFLOW_COMPILE_ERGONOMICS.md)** (testable acceptance criteria for phase **3**).

---

## 1. Scope: “graph construction and mapping”

| Phase | Where it happens | Bridge responsibility |
| ----- | ---------------- | --------------------- |
| **Compile** | `compile_replayt_workflow(workflow, …)` | Preconditions on `workflow` before `StateGraph` wiring (initial state, registered handler for initial step). |
| **Routing / transitions** | Conditional edges during `invoke` | After a handler returns, bridge checks `allows_transition` and resolves `replayt_next` to the next node or `END`. |
| **Inbound state** | `initial_bridge_state`, each step, checkpointer wrapper | Specified in **STATE_PAYLOAD_VALIDATION**; errors are **`BridgeStateValidationError`** (generic messages). |

**Version skew**

- **Unsupported `bridge_state_schema_version`** or limit violations → **`BridgeStateValidationError`** (see STATE_PAYLOAD_VALIDATION).
- **Stale or corrupt checkpoint blobs** → **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** (durable store skew vs routing).
- **Unsupported replayt or LangGraph major** outside declared ranges in `pyproject.toml` → compatibility process in **[DESIGN_PRINCIPLES.md — Dependency and Pin Policy](DESIGN_PRINCIPLES.md#dependency-and-pin-policy)**; the bridge does not define a dedicated “version skew” exception for upstream majors beyond normal import/runtime failures from upstream.

---

## 2. Implemented behavior (post §3)

| Situation | Raises | Message / notes | Structured log event |
| --------- | ------ | ---------------- | --------------------- |
| `workflow.initial_state` falsy | `BridgeWorkflowCompileError` (`ValueError` subclass) | Same message as former `ValueError` | None at bridge (pre-graph) |
| `initial_state` not a `@workflow.step` | `BridgeWorkflowCompileError` | Same message as former `ValueError` | None at bridge |
| Handler return names unknown step | `BridgeRoutingError` (`code` **`unknown_next`**) | Substring **`unknown next state`**; includes step names and expected set | `unknown_next` via `emit_bridge_record` |
| Handler return violates declared edges | `BridgeTransitionError` (`code` **`undeclared_transition`**) | Substring **`undeclared transition`**; includes step name and `allowed=` targets | `transition_invalid` |
| Inbound `ReplaytBridgeState` invalid | `BridgeStateValidationError` | Generic stable string per STATE_PAYLOAD_VALIDATION | May attach validation context per that spec |
| LangGraph `StateGraph.compile` / runtime | LangGraph / stdlib | Upstream message | Not bridge-originated |
| `CompiledStateGraph.invoke` / `ainvoke` with **missing** `context`, **missing** `runner` key, **`runner=None`**, **wrong-`Workflow` `Runner`**, or non-dict `context` | `BridgeInvokeContextError` | Substring **`replayt bridge invoke context`**; `code` is **`missing_runner`** or **`runner_workflow_mismatch`**; names `invoke` / `context` / `runner` / `Workflow` pairing; see §3.4 (no raw `context` payloads) | None at bridge (step entry) |

**Secrets and messages:** Routing and transition errors (`BridgeRoutingError`, `BridgeTransitionError`) include **step names** and **allowed targets** in `str(exc)` (non-secret workflow structure). They **must not** include raw `context` values, secrets, or unredacted attachments. (Structured logs that include `context` use the redaction pipeline — **[LOG_REDACTION.md](LOG_REDACTION.md)**.)

---

## 3. Target contract (Builder — post-implementation)

### 3.1 Stable exception types

Integrators must be able to distinguish **compile-time workflow misuse**, **transition contract violations**, **routing to an unknown step**, and **misconfigured `invoke` runtime context** (`runner` wiring) without parsing arbitrary text.

**Required**

1. **Public** exception types (exported from `replayt_langgraph_bridge` and listed in **`docs/API.md`** / `__all__` together).
2. **Stable `type(exc)`** across patch releases for the same failure mode (semver: breaking rename/removal only on major or documented 0.x bump per project practice).
3. **`str(exc)`** remains **safe for logs and UI**: no raw integrator `context` payloads, no checkpoint blobs, no tokens; step names and declared graph structure are allowed (same policy as today’s messages).

**Recommended shape** (exact names are normative once merged; adjust only via CHANGELOG + API.md):

| Type | Base | Failure mode |
| ---- | ---- | ------------ |
| `BridgeWorkflowCompileError` | `ValueError` | Missing `set_initial` / invalid initial step registration (today’s `ValueError` cases). |
| `BridgeTransitionError` | `BridgeGraphMappingError`* | Handler return not allowed by `note_transition` / `allows_transition` (today substring `undeclared transition`). |
| `BridgeRoutingError` | `BridgeGraphMappingError`* | `replayt_next` names a step not on the workflow (today substring `unknown next state`). |
| `BridgeInvokeContextError` | `Exception` | Missing or invalid LangGraph **`invoke`** **`context`** / **`runner`** before step execution (§3.4). |

\*`BridgeGraphMappingError` is a shared **public** base for mapping/routing failures (subclass `Exception`; does not need to inherit `RuntimeError`). Subclasses may set a **stable** string attribute e.g. `code: Final[Literal["undeclared_transition", "unknown_next"]]` for metrics — optional but encouraged if a single handler wants to branch without `isinstance` chains.

**Acceptable alternative:** One public type `BridgeGraphMappingError` with **documented** `code` values for the two routing cases **instead of** separate subclasses, if `__all__` and tests still expose a stable programmatic discriminator.

### 3.2 Substrings for tests

Tests **must** assert **`type(exc)`** (or `code` if using the single-type alternative) **and** keep **`pytest.raises(..., match=…)`** on a **short, stable** phrase. Implemented messages retain **`unknown next state`** and **`undeclared transition`** (see **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** §3.2).

### 3.3 Upstream exceptions

The bridge **may** let **LangGraph** or **replayt** exceptions propagate unchanged when the bridge does not translate the failure (e.g. internal LangGraph compile errors). Document any **new** wrapped/propagated cases in this file and in **`compile_replayt_workflow`** docstring.

### 3.4 Runtime `invoke` context (`runner` wiring)

**Contract:** The compiled graph’s LangGraph **runtime context** must supply a configured replayt **`Runner`** for the **same** `Workflow` (and store) the graph was built from: **`invoke(..., context={"runner": runner})`** (or the async equivalent). This is distinct from **compile-time** validation (§2) and from **routing** errors (`replayt_next`).

**Shipped behavior:** Validation runs at step-node entry in **`graph.py`** (`_require_invoke_runner`) **before** `RunContext` construction or `runner._current_state` assignment.

1. **Choke point** — `runner` must be present, non-`None`, a **`replayt.runner.Runner`**, and (for supported replayt **0.4.x**) `runner.workflow is` the same **`Workflow`** instance passed to **`compile_replayt_workflow`**. If **`Runner.workflow`** is absent or the identity check is unreliable in a future replayt release, narrow or drop the mismatch check and record the rationale in **CHANGELOG** / an issue.
2. **Public exception** — **`BridgeInvokeContextError`** (subclass **`Exception`**, exported in **`__all__`** and **`docs/API.md`**) with:
   - **`str(exc)`** that names **`invoke`**, **`context`**, **`runner`**, and **`Workflow`** pairing; points to **`docs/GRAPH_CONSTRUCTION_ERRORS.md`** §3.4.
   - **Stable substring** for **`pytest.raises(..., match=…)`:** **`replayt bridge invoke context`** (pinned here and in **REPLAYT_BOUNDARY_TESTS** §3.2).
   - **No** raw `context` dict, secrets, or checkpoint payloads.
3. **`code`** — Instance attribute on the exception: **`missing_runner`** (omitted / empty / wrong-type context, missing key, `None` runner, or non-`Runner` value) or **`runner_workflow_mismatch`** (runner bound to a different workflow than the compiled graph).
4. **Cause chain** — Primary surface is **`BridgeInvokeContextError`**; no misleading **`KeyError`** / **`AttributeError`** as the raised type for these cases.

**Tests:** **`tests/test_bridge_graph.py`** covers omitted `context`, `context={}`, `context={"runner": None}`, and wrong-`Workflow` **`Runner`**; asserts **`type(exc)`**, **`match=`** on **`replayt bridge invoke context`**, and **`code`** where applicable.

### 3.5 Compile-time `KeyError` chaining (`initial_state` not registered)

When **`workflow.initial_state`** names an unregistered step, the implementation may catch **`KeyError`** from **`workflow.get_handler`** and re-raise **`BridgeWorkflowCompileError`** with **`from e`**. Integrators may see **PEP 415** exception chaining in tracebacks. **Target:** keep **`BridgeWorkflowCompileError`** as the **raised** type; message remains the stable **`not a registered`** phrasing (§2). Optional Builder polish: ensure **`str(exc)`** alone is sufficient for common cases without requiring expand of **`__cause__`**.

---

## 4. Observability and optional logging

### 4.1 Structured logging (implemented path)

- **Logger:** `bridge_logger` argument or default from `get_bridge_logger()` (name `replayt_langgraph_bridge`).
- **Emission:** Lifecycle events (`step_completed`, `transition_invalid`, `unknown_next`, handler errors, etc.) use **`emit_bridge_record`**; attachments are redacted per **[LOG_REDACTION.md](LOG_REDACTION.md)**.
- **Default safety:** `redact=True` by default; `redact=False` emits a **runtime warning** and is not recommended for production.
- **“Optional” for integrators:** Logging is **off** for backends that have no handlers configured (stdlib logging behavior). Integrators who enable handlers receive structured records; those who want silence use logger levels, **`logging.NullHandler`**, or a no-op logger — document the pattern in **`README.md`** or **`docs/API.md`** in the same change set that touches behavior.

### 4.2 Optional diagnostic hook (if added)

If the Builder adds an **explicit** callback or debug flag beyond stdlib logging:

- It must be **opt-in** (default off).
- Any user-supplied hook that receives state-like data must receive **post-redaction** payloads **or** the doc must state clearly that callers **must not** log raw input (and tests must prove no secret literals leak under default config).

No hook is **required** for backlog completion if §4.1 patterns are documented.

### 4.3 Optional large-graph advisory (warnings or log) — spec for builders

If maintainers add a **cheap** advisory when compiled graphs are very large (e.g. `warnings.warn` or a single **high-level** log record, not per-node spam), **all** of the following are **normative for that feature**:

1. **Opt-in or bounded noise** — Either the advisory is **off by default** and enabled only by an **explicit** integrator choice (documented keyword argument, environment variable, or similar), **or** it may emit **at most once per interpreter process** for a given advisory class (first crossing of the threshold only; subsequent compiles stay silent unless the spec documents a reset). **Do not** default to unbounded repeated warnings on every `compile_replayt_workflow` call for the same process.
2. **No new failure mode** — Threshold crossing remains **non-fatal**; compilation succeeds unless independent validation fails.
3. **Tests** — Add a **small** automated test that proves the opt-in or **once-per-process** contract (e.g. `pytest` + `warnings.catch_warnings`, or `caplog` with a stable logger/message fragment). The test must **not** require network credentials or the **`demo`** extra.
4. **Docs and changelog** — Document the switch, thresholds, and exact `warning` category or log record shape in this file (or **`docs/API.md`** under **`compile_replayt_workflow`**) and add **`CHANGELOG.md` — Unreleased** when the behavior is user-visible.

Exact numeric thresholds are **not** fixed by this spec; choose conservative “high” values, document them next to the implementation, and tie release notes to any later change.

**Shipped behavior (this repo):** After a successful ``compile_replayt_workflow``, if ``len(workflow.step_names())`` is **≥ 256** (constant ``_LARGE_GRAPH_STEP_THRESHOLD`` in ``replayt_langgraph_bridge.graph``), the bridge issues ``warnings.warn(..., BridgeLargeGraphWarning)`` **at most once per process**; later compiles in the same interpreter stay silent. Integrators may filter on ``BridgeLargeGraphWarning`` (re-exported from ``replayt_langgraph_bridge``).

---

## 5. Non-normative guidance: graph size, shape, and profiling

This section is **guidance only**. It does **not** define new bridge limits beyond **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** (inbound dict size, nesting depth, walk limits). Integrators remain responsible for measuring their own workloads.

### 5.1 How the bridge maps `Workflow` size to LangGraph structure

For a replayt `Workflow` with **N** registered steps (`workflow.step_names()`):

- The compiled graph contains **N** LangGraph nodes (one per step) plus the framework **`START`** edge into **`workflow.initial_state`**.
- Each step node is wired with **conditional routing** to **every** step name and **`END`** (see `compile_replayt_workflow` in `graph.py`). So compile-time work and internal graph metadata scale with **N** in the ordinary sense of “more steps → larger graph,” and routing tables are **dense** with respect to declared step names (not a sparse DAG-only layout).

**“Deep nesting” (two meanings):**

- **Control-flow depth** — The bridge does not build a nested tree of subgraphs per replayt step; steps are **flat** nodes. Logical depth (long chains of transitions) still implies **long runs** and larger checkpoint histories, not deeper *compile* nesting.
- **Payload nesting** — Shallow merge and validation limits on `ReplaytBridgeState["context"]` are normative in **STATE_PAYLOAD_VALIDATION** (e.g. nesting depth and walk limits). Hitting those limits raises **`BridgeStateValidationError`**, not compile errors.

### 5.2 Practical expectations (orders of magnitude)

There is **no** published hard maximum step count: behavior depends on **Python**, **LangGraph**, and host memory. As **rule-of-thumb** guidance:

- **Tens to low hundreds of steps** are routinely cheap to compile on a developer laptop.
- **Thousands of steps** may still compile but can be noticeably slow or memory-heavy; treat this as a signal to **profile** and to split workflows or generation strategies if compile latency matters.

Adjust expectations when steps are generated programmatically (meta-workflows).

### 5.3 Profiling and integrator-owned tuning

To measure **compile vs first `invoke`** cost:

- Use **Python** profilers (`cProfile`, `pyinstrument`, etc.) around `compile_replayt_workflow` and a representative `invoke`.
- Consult **LangGraph** release notes and docs for **`StateGraph` / `compile`** performance characteristics on your pinned version.
- If only **runtime** is slow, distinguish **routing** and **handler** work from **bridge** overhead using logs and application metrics.

---

## 6. Product backlog acceptance mapping

| Backlog criterion | Done when (normative) |
| ----------------- | ---------------------- |
| **Documented error behavior** for invalid input, unsupported features, and version skew (as applicable) | This doc + `compile_replayt_workflow` / `initial_bridge_state` docstrings aligned; cross-links from **API.md**, **CHECKPOINT_PERSISTENCE** (routing vs persistence), **DESIGN_PRINCIPLES** (errors bullet). |
| **Tests assert stable exception types or error codes** for representative failure cases | At least: **unknown next**, **undeclared transition**, **compile without `set_initial`**, **invalid initial step**; assert public type or `code`; `match=` per §3.2. Prefer extending **`tests/test_bridge_graph.py`** (or sibling) so replayt-boundary docstrings stay accurate. |
| **Optional logging hook or documented pattern** does not emit sensitive data by default | **LOG_REDACTION** defaults + §4.1 pattern documented; tests continue to prove representative secrets do not appear in emitted records under default redaction (existing **`tests/test_log_redaction.py`** obligations). |
| **Large-workflow compile ergonomics** (docs + optional advisory) | **§5** (non-normative scale guidance) present; pointer from **`docs/API.md`** to this doc; **§4.3** satisfied if an advisory is implemented; **`CHANGELOG.md`** updated for any user-visible switch or default behavior; full checklist in **[BACKLOG_LARGE_WORKFLOW_COMPILE_ERGONOMICS.md](BACKLOG_LARGE_WORKFLOW_COMPILE_ERGONOMICS.md)**. |

---

## 7. Builder checklist (implementation gate)

The first graph-mapping hardening pass is merged; use the list below as a **regression gate** when editing compile or routing.

1. Keep §3 types (or single type + `code`) wired from `graph.py`; **`__all__`**, **`docs/API.md`**, **`README`** Public API stay aligned when exports change.
2. Routing cases stay on **`BridgeRoutingError`** / **`BridgeTransitionError`** (not bare **`RuntimeError`**); compile cases stay on **`BridgeWorkflowCompileError`** (still a **`ValueError`** subclass) unless **CHANGELOG** documents a deliberate break.
3. Add or adjust tests per §6 (acceptance mapping); keep **REPLAYT_BOUNDARY_TESTS** §3.2 aligned with this doc when assertion style changes.
4. **CHANGELOG.md** under **Unreleased**: note new exception types / any message changes integrators might catch.
5. Re-read **THREAT_MODEL** / **DESIGN_PRINCIPLES** security bullets for consistency (step names OK; secrets not in `str(exc)`).
6. When touching **large-graph** advisories: follow **§4.3**; keep thresholds and opt-in documented; extend tests per **BACKLOG_LARGE_WORKFLOW_COMPILE_ERGONOMICS**.
7. **`invoke` context:** Keep §3.4 (**`BridgeInvokeContextError`**, pinned substring, tests) aligned with **`graph.py`**; extend **`compile_replayt_workflow`** / **`docs/API.md`** when invoke guidance changes.

---

## 8. Related documents

- **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** — inbound dict validation.
- **[LOG_REDACTION.md](LOG_REDACTION.md)** — structured log redaction.
- **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** — checkpoint failures vs live routing errors.
- **[API.md](API.md)** — public export set.
- **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** — pytest message conventions.
- **[BACKLOG_LARGE_WORKFLOW_COMPILE_ERGONOMICS.md](BACKLOG_LARGE_WORKFLOW_COMPILE_ERGONOMICS.md)** — backlog acceptance criteria (scale docs + optional warning hook).
