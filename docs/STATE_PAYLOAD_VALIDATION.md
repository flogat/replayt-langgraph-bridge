# Inbound bridge state: validation and safe failure (normative spec)

This document defines **what the bridge guarantees** for the
**“Harden deserialization of replayt state mapped into LangGraph”** work.
It is the contract for **untrusted inbound** `ReplaytBridgeState`-shaped data: initial `invoke` input,
checkpoint-resumed channel state that the bridge consumes, and any other **public** path that copies
`state["context"]` into replayt’s `RunContext.data` (or equivalent).

**Status:** Implemented in `replayt_langgraph_bridge.state_validation` and wired from `graph.py`
(`validate_inbound_bridge_state`, `BridgeValidatingCheckpointSaver`). CI locks behavior in
`tests/test_state_payload_validation.py`. Extended **parametrized** regression coverage is specified in **§9**.

---

## 1. Goals

1. Treat inbound graph/channel payloads as **untrusted**: limit **size**, **depth**, and **shape** before
   the bridge applies them to runtime state.
2. **Fail closed**: invalid input is rejected **before** step handlers run and **before** the bridge
   mutates `RunContext.data` from that payload.
3. **No partial durable effects from rejected input**: a rejected validation must not leave the graph or
   checkpointer in a **new** partially-written state attributable to that rejected invocation (see §6).
4. **Least-information disclosure**: exceptions raised to callers use **stable, generic** messages;
   detailed diagnostics (paths, sizes, schema ids) go to **`logging.DEBUG`** on the bridge logger only when
   safe (no raw user payload values in debug lines unless behind an explicit integrator opt-in is out of
   scope for v1—default is **no payload content** in debug strings).

---

## 2. Public mapping surface (documentation obligation)

The following **must** document, in docstrings and in this file (README links here):

| Surface | What to document |
| -------- | ----------------- |
| `initial_bridge_state` | That `context=` is validated as **untrusted**; supported **schema version(s)**; **numeric limits** (§4); failure mode (§5). |
| `compile_replayt_workflow` | That compiled graphs expect validated inbound state consistent with this spec when entering bridge nodes from **outside** integrator-controlled handlers (initial input, resumed checkpoints). |
| Package-level docs (`__init__.py` / README **Public API**) | Pointer to this spec and a one-line summary of limits + schema version. |

Replayt’s `Workflow` / `Runner` objects remain **integrator-controlled**; this spec targets **serialized or
foreign-supplied** dict-shaped state crossing the bridge boundary, not the Python objects the integrator
constructs in-process.

---

## 3. Schema version

- **Field name (normative):** top-level `bridge_state_schema_version`, type `int`.
- **Semantics:** Identifies the **bridge wire format** for `ReplaytBridgeState`, not replayt’s internal
  workflow schema.
- **Supported set:** Document the supported integers in docstrings (e.g. `{1}` initially).
- **Default when omitted:** Treat as version **`1`** for backward compatibility **unless** a future bridge
  release explicitly documents a breaking change that requires the field.
- **Unknown version:** Any explicit integer **not** in the supported set → **validation error** (test:
  e.g. `999999`).
- **Type errors:** Non-integer or missing when required by a future version → validation error.

---

## 4. Size and shape limits (concrete targets for Builder)

Limits apply to the **inbound** `ReplaytBridgeState` dict **after** Python has constructed it (the bridge
validates Python objects; wire formats like JSON are upstream of this layer).

Recommended **initial** constants (tune only with threat-model review and CHANGELOG note):

| Limit | Suggested value | Notes |
| ----- | ----------------- | ----- |
| Max **nesting depth** for `context` values | `32` | Count each dict/list/tuple level; depth of primitive `0`. |
| Max **distinct nodes** visited during walk | `50_000` | Count dict keys, list elements, set items once each when traversing for depth/size. |
| Max **total string bytes** (utf-8) across all `str` values in `context` | `4_194_304` (4 MiB) | Prevents huge text blobs in context. |
| Max **entries** in `context` (top-level keys) | `10_000` | Shallow key count. |
| `replayt_next` | `str`, length ≤ `1024` after `str()` | Must not embed megabyte strings. |

**Malformed nested structures** (all must yield validation errors, with tests):

- **Cycles** in dict/list (e.g. `a["self"]=a`).
- **Disallowed types** inside `context` values: anything not safely serializable in the bridge’s supported
  subset (at minimum: reject `bytes`, `bytearray`, `memoryview`, callables, non-string/non-number
  non-collection custom instances; **exact** allowlist is implementation-defined but **must** be documented
  in module docstrings).
- **Wrong top-level shape:** missing `context` or `replayt_next`, or `context` not a `dict`.

**Oversize payload** (test): construct a payload that exceeds **one** of the table limits (e.g. depth
`33` or string total `4 MiB + 1`) and assert rejection.

---

## 5. Errors and logging

- **Public exception type:** A single dedicated type (e.g. `BridgeStateValidationError`) subclassing
  `ValueError` **or** `ValueError` itself—pick one in implementation and **export** it from the public
  package surface if integrators need to catch it; document in README.
- **Public `str(exception)`:** Generic, stable text (e.g. “Invalid bridge state” / “Unsupported bridge
  state schema version”) **without** embedding user data, step names from payload, or dump fragments.
- **Debug logging:** `logger.debug("...", extra={...})` may include structured fields such as
  `reason_code`, `limit_name`, `observed_depth`—**not** raw context values by default.

**Transition routing** errors (`BridgeRoutingError`, `BridgeTransitionError`; step names, allowed targets in `str(exception)`) are specified in **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)** and governed by **[THREAT_MODEL.md](THREAT_MODEL.md)** and **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)**;
this spec adds the **validation** layer **before** those paths execute on bad inbound state.

---

## 6. No partial mutation of graph or checkpoint (test obligations)

**Definition (for tests):** For a compiled graph with a **durable** checkpointer (e.g. LangGraph
`MemorySaver` or a small **file/sqlite** saver in tests), record **checkpoint count** or **serialized
fingerprint** before `invoke` / `ainvoke`.

When validation **fails** on the **first** application of inbound state for a thread:

1. **No step handler** from the integrator workflow runs (bridge rejects before `ctx.data.update` from
   that payload).
2. **Checkpoint store** is **identical** to pre-call state for that test scenario: no new checkpoint
   written **for that invocation** (LangGraph may or may not write metadata—tests should assert the
   property that matters: **no persisted channel state** from the rejected payload; use the same
   checkpointer the project already uses in security/graph tests).

For **resume** scenarios: if validation fails on resumed state, the test must show the **previous**
good checkpoint remains the latest usable snapshot (no corrupting overwrite).

---

## 7. Builder-facing acceptance checklist

Map backlog acceptance criteria to verifiable items:

- [x] **Docs:** `initial_bridge_state`, `compile_replayt_workflow`, README **Public API** list **max limits**
      and **supported `bridge_state_schema_version`** values (link here).
- [x] **Tests:** **Oversize** payload rejected; **unknown schema version** rejected; **malformed nested**
      (cycle, disallowed type, excessive depth) rejected.
- [x] **Tests:** Rejected first invoke does **not** run handlers and does **not** advance durable checkpoint
      state (§6).
- [x] **CHANGELOG:** User-visible behavior and any new public exception type documented under
      **Unreleased**.

**Extended suite (Mission Control — State payload validation fuzz and regression):** criteria **§9**; **§9.6**
checklist in **§9** records completion for Mission Control `945d5aa3-41cb-4806-a49b-8756186e7046`.

---

## 8. Related documents

- **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** — Persistence scope, supported checkpointer pattern for langgraph 1.1.x, limitations, and failure modes beyond inbound dict validation.
- **[THREAT_MODEL.md](THREAT_MODEL.md)** — Assets, trust boundaries, checkpoint storage.
- **[HOSTED_DEPLOYMENT_AUTHZ.md](HOSTED_DEPLOYMENT_AUTHZ.md)** — Deployment topologies and controls when checkpoints or graph APIs leave a single trusted process.
- **[LOG_REDACTION.md](LOG_REDACTION.md)** — Bridge-originated log redaction (orthogonal to payload validation).
- **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** — Security considerations summary.

---

## 9. Fuzz and regression test suite (parametrized boundaries)

This section is the **normative acceptance contract** for backlog **State payload validation fuzz and regression suite** (Mission Control `945d5aa3-41cb-4806-a49b-8756186e7046`). It **does not** change §4 limits or §5 public error strings; it requires **tighter automated coverage** so boundary changes fail CI with **clear, contract-named failures**.

### 9.1 Scope and placement

| Topic | Requirement |
| ----- | ----------- |
| **Primary module** | Extend **`tests/test_state_payload_validation.py`** unless a split is justified (e.g. file size); avoid broad refactors—prefer **`@pytest.mark.parametrize`** and small helpers shared inside that module. |
| **CI / install** | Tests run under the default **`uv run pytest`** invocation (**`[dev]`** only, no **`demo`** extra), same as the rest of the suite. |
| **“Fuzz” meaning** | **Deterministic** boundary and malformed-input matrices: exact limits ± 1, representative disallowed types, and schema-type skew. **Out of scope** for this backlog: random/property-based fuzzers, network I/O, or vendor LLM calls. Optional follow-up: **`hypothesis`** behind a documented marker is allowed only if it stays fast and default-CI-clean. |
| **Constants** | Parametrized cases **must** derive numeric boundaries from the same **`replayt_langgraph_bridge.state_validation`** exports the implementation uses (e.g. `MAX_CONTEXT_NESTING_DEPTH`, `MAX_CONTEXT_STRING_BYTES`, `MAX_CONTEXT_WALK_NODES`, `MAX_CONTEXT_TOP_LEVEL_KEYS`, `MAX_REPLAYT_NEXT_LEN`, `SUPPORTED_BRIDGE_STATE_SCHEMA_VERSIONS`) so limit tweaks update tests mechanically. |

### 9.2 Boundary size parametrization (minimum matrix)

Each row must be covered with **`pytest.mark.parametrize`** (or an equivalent table-driven pattern) so **at-limit accepts** and **over-limit rejects** (or the documented one-sided expectation) are visible in pytest output.

| Dimension | Accept case | Reject case | Public `str(exception)` (§5) |
| --------- | ----------- | ----------- | ---------------------------- |
| **`context` nesting depth** | Depth equal to **`MAX_CONTEXT_NESTING_DEPTH`** at deepest leaf | Depth **`MAX_CONTEXT_NESTING_DEPTH + 1`** | `Invalid bridge state` |
| **Total UTF-8 bytes of all `str` values in `context`** | Sum equal to **`MAX_CONTEXT_STRING_BYTES`** | Sum **`MAX_CONTEXT_STRING_BYTES + 1`** | `Invalid bridge state` |
| **Walk node count** | **`MAX_CONTEXT_WALK_NODES`** distinct visited nodes (dict keys / sequence elements / set items per implementation walk) | **`MAX_CONTEXT_WALK_NODES + 1`** | `Invalid bridge state` |
| **Top-level `context` keys** | **`MAX_CONTEXT_TOP_LEVEL_KEYS`** keys | **`MAX_CONTEXT_TOP_LEVEL_KEYS + 1`** | `Invalid bridge state` |
| **`replayt_next` length** | After `str()`, length **`MAX_REPLAYT_NEXT_LEN`** | Length **`MAX_REPLAYT_NEXT_LEN + 1`** | `Invalid bridge state` |

**Implementation hint:** shallow wide dicts, fan-out lists, or balanced trees can hit node limits without exceeding depth or string caps; reuse or add helpers next to **`_deep_nest_dict`** in the test module.

### 9.3 Schema version and malformed wire values

| Case | Expected | Public message substring (`pytest.raises(..., match=...)`) |
| ---- | -------- | ------------------------------------------------------------ |
| Explicit **unsupported** int (not in **`SUPPORTED_BRIDGE_STATE_SCHEMA_VERSIONS`**) | `BridgeStateValidationError` | `Unsupported bridge state schema version` |
| **`bridge_state_schema_version` present but wrong type** (`str`, `float`, `bool`, `None`, list, …) — anywhere the implementation resolves schema (top-level state **and** `__start__` channel merge per **`validate_input_checkpoint_channel_values`**) | `BridgeStateValidationError` | `Invalid bridge state` |
| **Omitted** version | Treated as **`1`** (§3); valid minimal payload still passes | — |
| **Explicit supported version** (e.g. **`1`**) | Passes when shape is otherwise valid | — |

### 9.4 Checkpoint non-mutation invariants (regression)

Keep or supersede existing graph-level tests with a **parametrized** table where practical:

1. **First `invoke` rejection** — Invalid inbound state: **no** workflow step handler runs; **no** new durable checkpoint tuple for that thread (same pattern as current **`MemorySaver.list` / `get_tuple` assertions in §6).
2. **Resume rejection** — After one good **`invoke`**, a second **`invoke`** with invalid state: checkpoint **count** and **latest checkpoint id** unchanged; channel values do not pick up corrupting fields from the rejected payload (align with existing **`bridge_state_schema_version` channel** assertions).

**Optional extension (not required for done):** repeat (1) or (2) with a **disk/sqlite** saver if the project already carries a **`[dev]`**-available checkpointer for deterministic tests (**[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)**, **[BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP.md](BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP.md)**).

### 9.5 Actionable failures (project conventions)

**Bridge inbound validation** is **not** a replayt-upstream contract; it follows **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** only where tests also exercise **replayt** APIs (e.g. **`Workflow`**, **`Runner`**, **`JSONLStore`**).

| Layer | Rule |
| ----- | ---- |
| **Public exception text** | Remains the **stable generic** strings in §5 (`Invalid bridge state` / `Unsupported bridge state schema version`). **`pytest.raises(..., match=...)`** must use those substrings (or full strings), not ad hoc phrases. |
| **Test docstrings** | Each parametrized scenario (or group) cites **this document** and the **§4 table row** or **§9.3 row** under test (e.g. “STATE_PAYLOAD_VALIDATION §9.2 walk node limit”). |
| **Non-parametrized asserts** | When asserting checkpoint ids, handler flags, or log content, use **two-argument `assert`** or messages that name the invariant (e.g. `STATE_PAYLOAD_VALIDATION §6: checkpoint id unchanged after rejected resume`). |
| **Debug logging** | Keep or extend coverage that **DEBUG** records do **not** embed raw payload secrets (see existing **`test_debug_log_emits_without_payload_values`** pattern). |

### 9.6 Builder acceptance checklist (§9 completion)

- [x] **§9.2** — Parametrized boundary tests for all five dimensions (accept + reject) via exported limits.
- [x] **§9.3** — Parametrized or table-driven tests for unsupported version, bad types (including **`__start__`** path), omitted vs explicit supported version.
- [x] **§9.4** — Parametrized graph + checkpointer tests for first-invoke and resume non-mutation (minimum: **`MemorySaver`**).
- [x] **§9.5** — Docstrings and `match=` patterns satisfy the table above; no user data in public exception assertions beyond what §5 allows.
- [x] **CHANGELOG** — Add **`[Unreleased]`** bullet **only** if implementation changes **integrator-visible** validation behavior or messages; **spec-only** or **test-only** landings need no entry per **[CONTRIBUTING.md](../CONTRIBUTING.md)** unless maintainers deem the new regression suite noteworthy for release notes.

---
