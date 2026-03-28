# Replayt boundary tests (normative)

This document defines **what** integration-style tests must prove about the **replayt** side of the bridge, and **how** failures must read so maintainers can tell **which upstream contract moved** without digging through opaque stack traces.

**Audience:** Builders adding or tightening tests; reviewers judging backlog completion.

**Non-goals:** LangGraph runtime internals (covered indirectly via compiled graphs where needed); exhaustive replayt API coverage beyond what the bridge uses.

---

## 1. Scope: “replayt boundary” in this package

A **replayt boundary test** imports **replayt** and exercises **behavior that replayt owns** that the bridge relies on at compile or run time. The bridge implementation in `replayt_langgraph_bridge.graph` currently depends on these **documented replayt entry points** (see `src/replayt_langgraph_bridge/graph.py`):

| replayt symbol / module | Role at the boundary |
| ----------------------- | -------------------- |
| `replayt.workflow.Workflow` | Step registration, `set_initial`, declared transitions (`note_transition` / `edges`), handler lookup, `allows_transition`, `step_names`, optional `llm_defaults` / `meta` |
| `replayt.runner.Runner` | Passed via LangGraph `invoke(..., context={"runner": runner})`; bridge reads `run_id`, sets `_current_state`, constructs `RunContext` |
| `replayt.runner.RunContext` | `data` dict mirrored with graph `context`; `get` / `set`; handler invocation |
| `replayt.persistence` stores (e.g. `JSONLStore`) | **Optional** in tests that prove durable execution paths the integrator would use alongside `Runner` |

Tests that only import `replayt_langgraph_bridge` and mock replayt types are **not** replayt boundary tests for this backlog.

---

## 2. Backlog acceptance criteria (builder checklist)

Map the product backlog to concrete deliverables:

1. **At least one integration-style test** — Imports **replayt** and calls **supported replayt APIs** from the table above in a scenario that reflects real bridge usage (minimal `Workflow` + `Runner` + store is sufficient). The test must exercise a path that matters to the bridge (e.g. running steps, transitions, `RunContext.data` round-trip), not merely importing replayt.
2. **Actionable failure surface** — Every **assertion** that guards a replayt contract, and every **`pytest.raises`** for expected errors, must make the **contract name** obvious:
   - Prefer `pytest.raises(..., match="...")` with a substring that names the invariant (e.g. transition graph, `RunContext.data` shape, store persistence).
   - For plain `assert` failures, use the **two-argument form** `assert actual == expected, "contract: …"` **or** a named helper that raises with a message prefix such as `replayt boundary:` followed by the broken assumption.
   - Test **function or module docstrings** should state **which upstream obligation** is under test (one line is enough).
3. **CI** — New or updated tests live under `tests/` and run in the existing **`pytest`** job (`.github/workflows/ci.yml`, Python 3.11 and 3.12). No separate job is required. That job installs **`[dev]`** only; it must **not** require the optional **`demo`** extra (**[DESIGN_PRINCIPLES.md — Core vs demo extras](DESIGN_PRINCIPLES.md#core-vs-demo-extras-llm-clients-and-supply-chain)**).
4. **Demo-only tests** — If a test imports optional **LLM vendor** client packages that live under the **`demo`** extra, gate it with an **importorskip** / **`pytest.mark.skip`** when the extra is not installed, **or** isolate it in a module excluded from the default CI invocation (document which). Default CI must remain green on `pip install -e ".[dev]"` only.

**Note:** The repository already contains integration-style coverage in `tests/test_bridge_graph.py`. The backlog is **satisfied** only when **messages and docstrings** meet section 3; the Builder may **extend** that file or add a dedicated module such as `tests/test_replayt_boundary.py`—either is fine if the checklist above is met.

---

## 3. “Actionable message” rules

### 3.1 Required clarity

When a replayt-facing assertion fails, a maintainer reading the pytest output should be able to answer:

- **What contract** broke (e.g. “handler return must match `Workflow` edges”, “`RunContext.data` after step X”).
- **What observation** mismatched (expected vs actual), without opening the replayt source first.

**Anti-patterns:**

- Assertions with no message and generic inequality (`assert x == y` with no context).
- `pytest.raises(Exception)` or overly broad exception types without `match=` when a specific error is expected.
- Relying solely on a deep stack trace inside replayt to explain the failure.

### 3.2 Examples (illustrative, not exhaustive)

| Contract under test | Acceptable pattern |
| ------------------- | ------------------ |
| Handler return names a step that is not registered on the workflow | `pytest.raises(RuntimeError, match="unknown next state")` **and** docstring mentions routing / declared step names |
| Handler return violates `note_transition` / `allows_transition` | `pytest.raises(RuntimeError, match="undeclared transition")` **and** docstring mentions declared edges |
| Linear workflow mutates `RunContext.data` as expected | `assert out["context"]["n"] == 2, "replayt boundary: RunContext.data carries cumulative ctx.set across steps"` |
| `Workflow.set_initial` required before compile | `pytest.raises(ValueError, match="set_initial")` with docstring referencing `workflow.initial_state` |

### 3.3 Skips and upstream gaps

If a scenario cannot run because replayt lacks a public API (or CI environment limitation), use **`@pytest.mark.skip`** or **`pytest.skip`** with a **reason** that includes a **tracking issue URL** (GitHub or other). Do not leave silent `skip` without an issue reference.

### 3.4 Optional `demo` extra (LLM samples)

Tests that **require** packages from the **`demo`** optional extra must not break the **core + dev** install path. Prefer **`pytest.importorskip("openai")`** (or the relevant module) with a **reason** that names the **`demo`** extra, or a dedicated marker documented in **`CONTRIBUTING.md`**.

---

## 4. Traceability

When landing tests, ensure:

- At least one test module or class docstring references **this document** by path (`docs/REPLAYT_BOUNDARY_TESTS.md`).
- Tests that focus on **LangGraph checkpoint save/load or resume** (rather than replayt API contracts) should reference **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** in a docstring so persistence backlog traceability stays clear; replayt boundary rules in **this** file still apply when the test imports **replayt**.
- **CHANGELOG.md** under **Unreleased** notes user-visible or maintainer-visible testing improvements if the change is noteworthy (optional for pure message/docstring tightening; required if new files or new CI-visible scenarios are added—follow **`CONTRIBUTING.md`**).

---

## 5. Related documents

- **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** — Principle 1 (explicit contracts and integration boundaries).
- **[MISSION.md](MISSION.md)** — Success metrics for automated tests and clear logs.
- **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** — LangGraph checkpoint persistence scope, failure modes, and deterministic test obligations (complements replayt-focused rules here).
- **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** — Bridge **inbound state** contracts (separate from replayt upstream types).
