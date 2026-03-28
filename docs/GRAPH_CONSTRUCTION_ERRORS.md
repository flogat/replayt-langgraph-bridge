# Graph construction and mapping errors (normative)

This document specifies **bridge-owned** error behavior and observability when a replayt `Workflow` is **compiled** into a LangGraph graph and when **routing** (`replayt_next`) is interpreted during `invoke`. It implements the product backlog **Harden error surfaces and observability for graph construction** so Builders and Testers share one checklist.

**Non-goals:** Errors raised **inside** integrator step handlers (replayt-owned), **LangGraph** internals (except where the bridge calls `compile` and must document propagation), and **inbound channel state** validation — the latter remain in **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** (`BridgeStateValidationError`).

**Related:** **[LOG_REDACTION.md](LOG_REDACTION.md)** (structured logs), **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** (resume vs routing failures), **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** (assertion style for graph tests).

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

## 2. Current behavior (baseline — today)

Use this table when comparing diffs during implementation. **Exception types in the “Raises (today)” column are targets for replacement** per §3.

| Situation | Raises (today) | Message / notes (today) | Structured log event (today) |
| --------- | -------------- | ------------------------ | ------------------------------ |
| `workflow.initial_state` falsy | `ValueError` | `workflow.initial_state must be set (call workflow.set_initial)` | None at bridge (pre-graph) |
| `initial_state` not a `@workflow.step` | `ValueError` | `initial_state … is not a registered @workflow.step` | None at bridge |
| Handler return names unknown step | `RuntimeError` | Substring **`unknown next state`**; includes `from_step`, declared step names | `unknown_next` via `emit_bridge_record` |
| Handler return violates declared edges | `RuntimeError` | Substring **`undeclared transition`**; includes step name and `allowed=` targets | `transition_invalid` |
| Inbound `ReplaytBridgeState` invalid | `BridgeStateValidationError` | Generic stable string per STATE_PAYLOAD_VALIDATION | May attach validation context per that spec |
| LangGraph `StateGraph.compile` / runtime | LangGraph / stdlib | Upstream message | Not bridge-originated |

**Secrets and messages:** Routing and transition **`RuntimeError`** messages include **step names** and **allowed targets** (non-secret workflow structure). They **must not** include raw `context` values, secrets, or unredacted attachments. (Structured logs that include `context` use the redaction pipeline — **[LOG_REDACTION.md](LOG_REDACTION.md)**.)

---

## 3. Target contract (Builder — post-implementation)

### 3.1 Stable exception types

Integrators must be able to distinguish **compile-time workflow misuse**, **transition contract violations**, and **routing to an unknown step** without parsing arbitrary text.

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

\*`BridgeGraphMappingError` is a shared **public** base for mapping/routing failures (subclass `Exception`; does not need to inherit `RuntimeError`). Subclasses may set a **stable** string attribute e.g. `code: Final[Literal["undeclared_transition", "unknown_next"]]` for metrics — optional but encouraged if a single handler wants to branch without `isinstance` chains.

**Acceptable alternative:** One public type `BridgeGraphMappingError` with **documented** `code` values for the two routing cases **instead of** separate subclasses, if `__all__` and tests still expose a stable programmatic discriminator.

### 3.2 Substrings for tests

Until types land, **`pytest.raises(..., match=…)`** uses the substrings **`unknown next state`** and **`undeclared transition`** (see **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** §3.2).

**After** types land, tests **must** assert **`type(exc)`** (or `code` if using the single-type alternative) **and** keep a **`match=`** on a **short, documented** phrase that remains stable (either the same substrings if preserved in `str(exc)`, or new documented phrases listed in this doc and in test docstrings).

### 3.3 Upstream exceptions

The bridge **may** let **LangGraph** or **replayt** exceptions propagate unchanged when the bridge does not translate the failure (e.g. internal LangGraph compile errors). Document any **new** wrapped/propagated cases in this file and in **`compile_replayt_workflow`** docstring.

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

---

## 5. Product backlog acceptance mapping

| Backlog criterion | Done when (normative) |
| ----------------- | ---------------------- |
| **Documented error behavior** for invalid input, unsupported features, and version skew (as applicable) | This doc + `compile_replayt_workflow` / `initial_bridge_state` docstrings aligned; cross-links from **API.md**, **CHECKPOINT_PERSISTENCE** (routing vs persistence), **DESIGN_PRINCIPLES** (errors bullet). |
| **Tests assert stable exception types or error codes** for representative failure cases | At least: **unknown next**, **undeclared transition**, **compile without `set_initial`**, **invalid initial step**; assert public type or `code`; `match=` per §3.2. Prefer extending **`tests/test_bridge_graph.py`** (or sibling) so replayt-boundary docstrings stay accurate. |
| **Optional logging hook or documented pattern** does not emit sensitive data by default | **LOG_REDACTION** defaults + §4.1 pattern documented; tests continue to prove representative secrets do not appear in emitted records under default redaction (existing **`tests/test_log_redaction.py`** obligations). |

---

## 6. Builder checklist (implementation gate)

1. Implement §3 types (or single type + `code`); wire `graph.py` raises; update **`__all__`**, **`docs/API.md`**, **`README`** Public API if exports change.
2. Replace bare **`RuntimeError`** for the two routing cases with the new surface; keep **`ValueError`** cases as **`BridgeWorkflowCompileError`** or strict subclasses with same messages for minimal churn.
3. Add or adjust tests per §5; ensure **REPLAYT_BOUNDARY_TESTS** §3.2 table references this doc for post-change assertion style.
4. **CHANGELOG.md** under **Unreleased**: note new exception types / any message changes integrators might catch.
5. Re-read **THREAT_MODEL** / **DESIGN_PRINCIPLES** security bullets for consistency (step names OK; secrets not in `str(exc)`).

---

## 7. Related documents

- **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** — inbound dict validation.
- **[LOG_REDACTION.md](LOG_REDACTION.md)** — structured log redaction.
- **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** — checkpoint failures vs live routing errors.
- **[API.md](API.md)** — public export set.
- **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** — pytest message conventions.
