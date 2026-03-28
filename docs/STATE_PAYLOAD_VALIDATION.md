# Inbound bridge state: validation and safe failure (normative spec)

This document defines **what the bridge must guarantee** once the
**“Harden deserialization of replayt state mapped into LangGraph”** backlog is implemented.
It is the contract for **untrusted inbound** `ReplaytBridgeState`-shaped data: initial `invoke` input,
checkpoint-resumed channel state that the bridge consumes, and any other **public** path that copies
`state["context"]` into replayt’s `RunContext.data` (or equivalent).

**Status:** Specification only. Behavior described here is **not** required to exist in the codebase until
the Builder lands the implementation; CI should gain tests that lock the behaviors below when code exists.

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

Existing **`RuntimeError`** messages for **transition routing** (step names, allowed targets) remain
governed by **[THREAT_MODEL.md](THREAT_MODEL.md)** and **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)**;
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

- [ ] **Docs:** `initial_bridge_state`, `compile_replayt_workflow`, README **Public API** list **max limits**
      and **supported `bridge_state_schema_version`** values (link here).
- [ ] **Tests:** **Oversize** payload rejected; **unknown schema version** rejected; **malformed nested**
      (cycle, disallowed type, excessive depth) rejected.
- [ ] **Tests:** Rejected first invoke does **not** run handlers and does **not** advance durable checkpoint
      state (§6).
- [ ] **CHANGELOG:** User-visible behavior and any new public exception type documented under
      **Unreleased**.

---

## 8. Related documents

- **[THREAT_MODEL.md](THREAT_MODEL.md)** — Assets, trust boundaries, checkpoint storage.
- **[LOG_REDACTION.md](LOG_REDACTION.md)** — Bridge-originated log redaction (orthogonal to payload validation).
- **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** — Security considerations summary.
