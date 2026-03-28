# Replayt boundary tests (normative)

This document defines **what** integration-style tests must prove about the **replayt** side of the bridge, and **how** failures must read so maintainers can tell **which upstream contract moved** without digging through opaque stack traces.

**Contract-style** (used in backlog titles): Tests that treat **replayt’s public API** as an external dependency the bridge consumes. They import supported **`replayt.*`** modules, exercise behaviors **`replayt_langgraph_bridge`** relies on (compile-time or run-time), and fail with messages that name **which compatibility assumption** broke—so an upstream **patch or minor** that changes those behaviors shows up as a **targeted** failure, not only a deep stack trace. They **do not** assert on private replayt internals or duplicate replayt’s own unit suite.

**Audience:** Builders adding or tightening tests; reviewers judging backlog completion.

**Non-goals:** LangGraph runtime internals (covered indirectly via compiled graphs where needed); exhaustive replayt API coverage beyond what the bridge uses.

---

## Product backlog: Add contract-style tests at the replayt boundary

Normative mapping from the product backlog acceptance criteria to this repository:

| Backlog criterion | Done when (normative) |
| ----------------- | ---------------------- |
| **At least one test module** explicitly targets replayt integration (imports **replayt**, exercises a **supported** public API). | At least one collected file under `tests/` has a **module docstring** that states the file covers **replayt boundary** / **consumer contract** behavior and points to **this document** (`docs/REPLAYT_BOUNDARY_TESTS.md`). The module **imports** `replayt` (or a documented submodule such as `replayt.workflow`, `replayt.runner`, `replayt.persistence`) in a way pytest collects—**top-level imports preferred**; lazy imports inside test functions are allowed if the docstring still makes the replayt-contract intent obvious. The module must call **supported** APIs from §1’s table (or successors documented here if the bridge’s `graph.py` dependencies change)—**not** private or undocumented replayt symbols. |
| **Failures produce actionable messages** (what assumption broke). | Every replayt-facing **assert** and **`pytest.raises`** follows §3 (contract-named messages, `match=` where applicable). |
| **Documented command** runs these tests **in CI alongside** unit tests. | **README** (dependency / CI bullets) and/or **CONTRIBUTING.md** state that contributors run **`pytest`** with **no extra path or marker** for the integrator-relevant suite. That matches **`.github/workflows/ci.yml`** job **`test`**, which runs **`pytest`** after **`pip install -e .[dev]`**—boundary tests are **not** a separate undocumented job or one-off script unless this document and those files are updated together to say so. |

Private replayt internals (underscore-prefixed objects, undocumented modules) are **out of scope** for contract-style coverage; if the bridge must depend on something not public, track it as a **compatibility risk** (issue / shim) rather than baking it into “contract” tests.

---

## Product backlog: Harden error surfaces and observability for graph construction

Normative mapping from the product backlog acceptance criteria to this repository (full error taxonomy and logging rules: **`docs/GRAPH_CONSTRUCTION_ERRORS.md`**):

| Backlog criterion | Done when (normative) |
| ----------------- | ---------------------- |
| **Documented error behavior** for invalid input, unsupported features, and version skew (as applicable) | **`docs/GRAPH_CONSTRUCTION_ERRORS.md`** + aligned docstrings on **`compile_replayt_workflow`** / **`initial_bridge_state`**; cross-links from **API.md**, **CHECKPOINT_PERSISTENCE**, **DESIGN_PRINCIPLES**. |
| **Tests assert stable exception types or error codes** for representative failure cases | Tests cover at least: unknown next step, undeclared transition, compile without **`set_initial`**, invalid initial step; assert **public type** or documented **`code`** attribute and use **`pytest.raises(..., match=…)`** per §3.2 and **GRAPH_CONSTRUCTION_ERRORS** §3.2. |
| **Optional logging hook or documented pattern** does not emit sensitive data by default | **LOG_REDACTION** defaults; integrator silence/verbosity pattern documented in **README** or **API.md**; representative-secret tests per **LOG_REDACTION** / **GRAPH_CONSTRUCTION_ERRORS** §4. |

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

## 2. Builder checklist (implementation gate)

Concrete deliverables for contract-style replayt boundary work (aligns with the product backlog table above):

1. **Module + scenario** — At least one `tests/` module meets the **module docstring** and **import** rules in the backlog table. Within that module, at least one test **calls** supported replayt APIs from the §1 table in a scenario that reflects real bridge usage (minimal `Workflow` + `Runner` + store is sufficient). The scenario must exercise a path that matters to the bridge (e.g. running steps, transitions, `RunContext.data` round-trip), not merely importing replayt.
2. **Actionable failure surface** — Every **assertion** that guards a replayt contract, and every **`pytest.raises`** for expected errors, must make the **contract name** obvious:
   - Prefer `pytest.raises(..., match="...")` with a substring that names the invariant (e.g. transition graph, `RunContext.data` shape, store persistence).
   - For plain `assert` failures, use the **two-argument form** `assert actual == expected, "contract: …"` **or** a named helper that raises with a message prefix such as `replayt boundary:` followed by the broken assumption.
   - Each **test function** docstring should state **which upstream obligation** is under test (one line is enough); the **module** docstring ties the file to this spec (see §4).
3. **CI / default suite** — Tests live under `tests/` and are collected by the same **`pytest`** invocation documented for contributors and run in **`.github/workflows/ci.yml`** job **`test`** (Python 3.11 and 3.12). No separate CI job is **required**. That job installs **`[dev]`** only; it must **not** require the optional **`demo`** extra (**[DESIGN_PRINCIPLES.md — Core vs demo extras](DESIGN_PRINCIPLES.md#core-vs-demo-extras-llm-clients-and-supply-chain)**).
4. **Demo-only tests** — If a test imports optional **LLM vendor** client packages that live under the **`demo`** extra, gate it with an **importorskip** / **`pytest.mark.skip`** when the extra is not installed, **or** isolate it in a module excluded from the default CI invocation (document which). Default CI must remain green on `pip install -e ".[dev]"` only.

**Implementation note:** `tests/test_bridge_graph.py` may already satisfy §2.1–2.2 if its module docstring, imports, and messages match this document. The Builder may **extend** that file or add a dedicated module (e.g. `tests/test_replayt_boundary_contracts.py`) when splitting **LangGraph checkpoint** scenarios from **pure replayt API** contracts improves clarity—either layout is acceptable if every checklist item and the product backlog table are satisfied.

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
| Handler return names a step that is not registered on the workflow | `pytest.raises(RuntimeError, match="unknown next state")` **and** docstring mentions routing / declared step names; after **`docs/GRAPH_CONSTRUCTION_ERRORS.md`** §3 is implemented, assert the **public** routing exception type (or `code`) **and** keep `match=` on a stable phrase documented there |
| Handler return violates `note_transition` / `allows_transition` | `pytest.raises(RuntimeError, match="undeclared transition")` **and** docstring mentions declared edges; after **GRAPH_CONSTRUCTION_ERRORS** §3, assert the **public** transition exception type (or `code`) **and** keep `match=` per that doc |
| Linear workflow mutates `RunContext.data` as expected | `assert out["context"]["n"] == 2, "replayt boundary: RunContext.data carries cumulative ctx.set across steps"` |
| `Workflow.set_initial` required before compile | `pytest.raises(ValueError, match="set_initial")` with docstring referencing `workflow.initial_state` |

### 3.3 Skips and upstream gaps

If a scenario cannot run because replayt lacks a public API (or CI environment limitation), use **`@pytest.mark.skip`** or **`pytest.skip`** with a **reason** that includes a **tracking issue URL** (GitHub or other). Do not leave silent `skip` without an issue reference.

### 3.4 Optional `demo` extra (LLM samples)

Tests that **require** packages from the **`demo`** optional extra must not break the **core + dev** install path. Prefer **`pytest.importorskip("openai")`** (or the relevant module) with a **reason** that names the **`demo`** extra, or a dedicated marker documented in **`CONTRIBUTING.md`**.

---

## 4. Traceability

When landing tests, ensure:

- At least one **module** docstring references **this document** by path (`docs/REPLAYT_BOUNDARY_TESTS.md`) and identifies the file as replayt-boundary / contract-style coverage (required for the “explicitly targets replayt integration” backlog criterion).
- Tests that focus on **LangGraph checkpoint save/load or resume** (rather than replayt API contracts) should reference **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** in a docstring so persistence backlog traceability stays clear; replayt boundary rules in **this** file still apply when the test imports **replayt**.
- **CHANGELOG.md** under **Unreleased** notes user-visible or maintainer-visible testing improvements if the change is noteworthy (optional for pure message/docstring tightening; required if new files or new CI-visible scenarios are added—follow **`CONTRIBUTING.md`**).

---

## 5. Related documents

- **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** — Principle 1 (explicit contracts and integration boundaries).
- **[MISSION.md](MISSION.md)** — Success metrics for automated tests and clear logs.
- **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** — LangGraph checkpoint persistence scope, failure modes, and deterministic test obligations (complements replayt-focused rules here).
- **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** — Bridge **inbound state** contracts (separate from replayt upstream types).
- **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)** — Compile and routing exception taxonomy, logging, and test obligations for the graph mapping backlog.
