# Replayt boundary tests (normative)

This document defines **what** integration-style tests must prove about the **replayt** side of the bridge, and **how** failures must read so maintainers can tell **which upstream contract moved** without digging through opaque stack traces.

**Contract-style** (used in backlog titles): Tests that treat **replayt’s public API** as an external dependency the bridge consumes. They import supported **`replayt.*`** modules, exercise behaviors **`replayt_langgraph_bridge`** relies on (compile-time or run-time), and fail with messages that name **which compatibility assumption** broke—so an upstream **patch or minor** that changes those behaviors shows up as a **targeted** failure, not only a deep stack trace. They **do not** assert on private replayt internals or duplicate replayt’s own unit suite.

**Audience:** Builders adding or tightening tests; reviewers judging backlog completion.

**Non-goals:** LangGraph runtime internals (covered indirectly via compiled graphs where needed); exhaustive replayt API coverage beyond what the bridge uses.

## Related documents

- **[BACKLOG_REPLAYT_05_READINESS.md](BACKLOG_REPLAYT_05_READINESS.md)** — **replayt 0.5+** consumer checklist (R1–R5) and inventory procedure.
- **[COMPATIBILITY_UPDATE_REPLAYT_05.md](COMPATIBILITY_UPDATE_REPLAYT_05.md)** — draft **Compatibility Update** issue body for filing when tracking **0.5.x**.

---

## Product backlog: Add contract-style tests at the replayt boundary

Normative mapping from the product backlog acceptance criteria to this repository:

| Backlog criterion | Done when (normative) |
| ----------------- | ---------------------- |
| **At least one test module** explicitly targets replayt integration (imports **replayt**, exercises a **supported** public API). | At least one collected file under `tests/` has a **module docstring** that states the file covers **replayt boundary** / **consumer contract** behavior and points to **this document** (`docs/REPLAYT_BOUNDARY_TESTS.md`). The module **imports** `replayt` (or a documented submodule such as `replayt.workflow`, `replayt.runner`, `replayt.persistence`) in a way pytest collects—**top-level imports preferred**; lazy imports inside test functions are allowed if the docstring still makes the replayt-contract intent obvious. The module must call **supported** APIs from §1’s table (or successors documented here if the bridge’s `graph.py` dependencies change)—**not** private or undocumented replayt symbols. |
| **Failures produce actionable messages** (what assumption broke). | Every replayt-facing **assert** and **`pytest.raises`** follows §3 (contract-named messages, `match=` where applicable). |
| **Documented command** runs these tests **in CI alongside** unit tests. | **README** (dependency / CI bullets) and/or **CONTRIBUTING.md** state that contributors run **`uv run pytest`** with **no extra path or marker** for the integrator-relevant suite. That matches **`.github/workflows/ci.yml`** job **`test`**, which runs **`uv run pytest`** after **`uv sync --frozen --extra dev`** (the same job runs **ruff** and the **mypy** package smoke per the workflow and **README**). Boundary tests are **not** a separate undocumented job or one-off script unless this document and those files are updated together to say so. |

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

## Product backlog: THREAT_MODEL drift guard and README/MISSION linkage contract

Normative mapping for keeping **[THREAT_MODEL.md](THREAT_MODEL.md)** discoverable from primary entry docs and structurally stable enough for security reviewers to trust cross-links.

| Backlog criterion | Done when (normative) |
| ----------------- | ---------------------- |
| **Lightweight contract test** (`tests/test_*_contract.py` pattern) | New module (recommended name: **`tests/test_threat_model_doc_linkage_contract.py`**) collected by default **`pytest`**. Module docstring names the **THREAT_MODEL documentation linkage** obligation and points to **this document** §6. Tests use **filesystem reads** only (no **`replayt`** import required). |
| **`docs/THREAT_MODEL.md` exists and carries agreed anchors** | File exists at repo-relative path **`docs/THREAT_MODEL.md`**. UTF-8 text contains **exactly** these Markdown level-2 heading lines (verbatim substrings; order-preserving when asserted as a sequence): **`## 1. Assets`**, **`## 2. Adversaries`**, **`## 3. Trust Boundaries`**, **`## 4. Mitigations`**, **`## 5. Explicit Non-Goals`**, **`## 6. Unsafe Fields`**, **`## 7. Recommendations for Integrators`**, **`## Links`**. First heading line of the file must remain **`# Threat Model: Checkpoint and State Data`**. |
| **`README.md` and `docs/MISSION.md` reference the threat model** | Each file’s UTF-8 text contains the case-sensitive substring **`THREAT_MODEL.md`** at least once (matches how **`tests/test_security_reporting_contract.py`** pins reporting text). |
| **Actionable failures** | Assertions (or helper raises) include message prefix **`THREAT_MODEL doc linkage contract:`** followed by which invariant broke (missing file, missing heading, missing README/MISSION substring). |
| **Contributor doc refresh rule** | Documented in §6.3 below; **no separate CONTRIBUTING.md convention** is required unless maintainers want a short pointer mirroring **`test_gitignore_contract.py`** (optional). |
| **`CHANGELOG.md`** | Per backlog: add an **Unreleased** bullet only when this work (or a follow-on edit) changes **integrator-facing** security narrative in **README** / **MISSION** / normative security docs—not for adding the contract test alone. |

---

## Product backlog: Human-in-the-loop cookbook (`interrupt_before` / `interrupt_after`)

Normative mapping for Mission Control item **`4b64a655-bb06-49e5-8912-61b06626a034`** (full checklist and reconciliation with existing tests: **`docs/BACKLOG_HITL_INTERRUPT_COOKBOOK.md`**).

| Backlog criterion | Done when (normative) |
| ----------------- | ---------------------- |
| **Copy-paste cookbook** for paused graphs (**LangGraph 1.1.x** + bridge **Runner** wiring) | **README** and/or **`docs/API.md`** include a fenced Python example per **BACKLOG_HITL_INTERRUPT_COOKBOOK §3.1** (`MemorySaver`, **`thread_id`**, **`interrupt_before` / `interrupt_after`**, two **`invoke`** calls, **`context={"runner": runner}`**). |
| **Automated interrupt coverage** | **`tests/test_bridge_graph.py`** (or adjacent): keep **`test_resume_second_invoke_uses_memory_checkpointer`**; add at least one test exercising **`interrupt_after`** per **BACKLOG_HITL_INTERRUPT_COOKBOOK §3.2** (deterministic, **`[dev]`** only, contract-named **`replayt boundary:`** messages). |
| **Changelog** | **CHANGELOG.md — Unreleased** when integrator-facing **`interrupt_*`** semantics or cookbook text ships (**BACKLOG_HITL_INTERRUPT_COOKBOOK §3.3**). |

---

## Product backlog: Optional disk-backed checkpoint round-trip (SQLite)

Normative mapping for Mission Control item **`255db7a8-876d-475d-8c69-cdb5f0c9fcc0`** (full checklist: **`docs/BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP.md`**).

| Backlog criterion | Done when (normative) |
| ----------------- | ---------------------- |
| **Focused pytest** with **non-network** LangGraph disk checkpointer (**SQLite** primary) | New or extended tests under **`tests/`** use an upstream **SQLite** (or documented disk) saver, **temp filesystem** paths, and **`compile_replayt_workflow`** + **`invoke`** + **`context={"runner": runner}`** per **BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP §3.2**. |
| **Save/load across process or graph re-compile** where feasible | At least **one** of cross-process resume or second **compile** against the same DB, per **BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP §2.2**; docstring explains skips. |
| **Default CI (`[dev]` only, `uv.lock`)** | **`uv sync --frozen --extra dev`** + **`uv run pytest`** (full suite, no **`demo`** extra); any new saver package is **`dev`**-scoped and **lockfile-pinned** per **BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP §3.1**. |
| **Replayt-facing assertions** | **§2–§3** of **this** document (**contract-named** messages) wherever **replayt** APIs are asserted. |
| **Platform constraints documented** | **CHECKPOINT_PERSISTENCE.md** §3 or §7 and/or test module docstring per **BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP §3.3**. |
| **CHANGELOG Unreleased** | Per **BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP §3.4** when implementation merges (not required for phase-2 spec-only edits). |

---

## Product backlog: Replayt 0.5 readiness checklist and boundary test updates

Normative mapping for Mission Control item **`8c5e0a89-66d8-4e11-ac7e-532b39f11156`** (full checklist, API inventory, pin decision, CI vs blockers: **`docs/BACKLOG_REPLAYT_05_READINESS.md`**).

| Backlog criterion | Done when (normative) |
| ----------------- | ---------------------- |
| **Compatibility Update issue filled out** | **R1** in **BACKLOG_REPLAYT_05_READINESS §2** — issue from **`.github/ISSUE_TEMPLATE/compatibility_update.md`** with **replayt** **0.5** target version, completed **Test Results** / **Impact** / **Required Changes**, plus template **Replayt 0.5+ compatibility** checklist (or equivalent) linking **BACKLOG_REPLAYT_05_READINESS**. |
| **Track public API vs `src/` and contract tests** | **R2** — inventory of **`replayt.*`** usage in **`src/replayt_langgraph_bridge/`** and replayt-facing **`tests/`** modules, reconciled to **0.5** public API; recorded in that issue. |
| **`pyproject` pin decision** | **R3** — decision documented in the issue and **`pyproject.toml`** (and **DESIGN_PRINCIPLES** / **README** when integrator-facing) updated on merge; comments justify the range. |
| **Green CI on prerelease or documented blockers** | **R4** — matrix-green evidence (3.11–3.13, frozen **`[dev]`** path per repo norms) **or** blocker list with upstream URLs in the issue. |
| **Boundary spec / §1 table** | **R5** — If new replayt surfaces are required, update **§1** table below and contract tests in the same change set; otherwise issue states **§1 unchanged** with rationale. |

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
3. **CI / default suite** — Tests live under `tests/` and are collected by the same **`uv run pytest`** invocation documented for contributors and run in **`.github/workflows/ci.yml`** job **`test`** (Python 3.11, 3.12, and 3.13). That job also runs **ruff** and the **mypy** smoke described in **README** and the workflow. No separate CI job is **required** for boundary tests. That job installs **`[dev]`** only; it must **not** require the optional **`demo`** extra (**[DESIGN_PRINCIPLES.md — Core vs demo extras](DESIGN_PRINCIPLES.md#core-vs-demo-extras-llm-clients-and-supply-chain)**).
4. **Demo-only tests** — If a test imports optional **LLM vendor** client packages that live under the **`demo`** extra, gate it with an **importorskip** / **`pytest.mark.skip`** when the extra is not installed, **or** isolate it in a module excluded from the default CI invocation (document which). Default CI must remain green on the **`[dev]`**-only frozen install (**`uv sync --frozen --extra dev`**, equivalent intent to editable **`[dev]`** without **`demo`**).

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
| Handler return names a step that is not registered on the workflow | `pytest.raises(BridgeRoutingError, match="unknown next state")` **and** assert `exc.value.code == "unknown_next"`; docstring mentions routing / declared step names (**GRAPH_CONSTRUCTION_ERRORS** §3.2) |
| Handler return violates `note_transition` / `allows_transition` | `pytest.raises(BridgeTransitionError, match="undeclared transition")` **and** assert `exc.value.code == "undeclared_transition"`; docstring mentions declared edges |
| Linear workflow mutates `RunContext.data` as expected | `assert out["context"]["n"] == 2, "replayt boundary: RunContext.data carries cumulative ctx.set across steps"` |
| `Workflow.set_initial` required before compile | `pytest.raises(BridgeWorkflowCompileError, match="set_initial")` (still a `ValueError` subclass) with docstring referencing `workflow.initial_state` |

### 3.3 Skips and upstream gaps

If a scenario cannot run because replayt lacks a public API (or CI environment limitation), use **`@pytest.mark.skip`** or **`pytest.skip`** with a **reason** that includes a **tracking issue URL** (GitHub or other). Do not leave silent `skip` without an issue reference.

### 3.4 Optional `demo` extra (LLM samples)

Tests that **require** packages from the **`demo`** optional extra must not break the **core + dev** install path. Prefer **`pytest.importorskip("openai")`** (or the relevant module) with a **reason** that names the **`demo`** extra, or a dedicated marker documented in **`CONTRIBUTING.md`**.

**First-party runnable samples** under **`examples/`** must **not** perform side effects at **import** time (so accidental **`tests/`** imports do not call the network). The **`examples/llm_node_graph.py`** contract is specified in **[BACKLOG_FIRST_PARTY_LLM_SAMPLE.md](BACKLOG_FIRST_PARTY_LLM_SAMPLE.md)** §3.1 and §3.6.

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
- **[THREAT_MODEL.md](THREAT_MODEL.md)** — Checkpoint/state threat model; **documentation linkage** contract in §6 of this file.
- **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** — LangGraph checkpoint persistence scope, failure modes, and deterministic test obligations (complements replayt-focused rules here).
- **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** — Bridge **inbound state** contracts (separate from replayt upstream types).
- **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)** — Compile and routing exception taxonomy, logging, and test obligations for the graph mapping backlog.
- **[BACKLOG_HITL_INTERRUPT_COOKBOOK.md](BACKLOG_HITL_INTERRUPT_COOKBOOK.md)** — **`interrupt_before` / `interrupt_after`** cookbook and test acceptance (Mission Control backlog `4b64a655-bb06-49e5-8912-61b06626a034`).
- **[BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP.md](BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP.md)** — Disk-backed (**SQLite**) checkpoint round-trip pytest and CI acceptance (Mission Control backlog `255db7a8-876d-475d-8c69-cdb5f0c9fcc0`).
- **[BACKLOG_FIRST_PARTY_LLM_SAMPLE.md](BACKLOG_FIRST_PARTY_LLM_SAMPLE.md)** — First-party **`examples/`** LLM sample, **`[demo]`** extra, CI boundaries, env vars, and redaction acceptance (Mission Control backlog `74a40ce9-cd64-4ab3-bda8-50296e094201`).
- **[BACKLOG_REPLAYT_05_READINESS.md](BACKLOG_REPLAYT_05_READINESS.md)** — **replayt 0.5** pin readiness, API inventory, Compatibility Update issue, CI vs upstream blockers (Mission Control backlog `8c5e0a89-66d8-4e11-ac7e-532b39f11156`).

---

## 6. THREAT_MODEL documentation linkage contract (normative)

This section is the **source of truth** for the backlog **THREAT_MODEL drift guard and README/MISSION linkage contract**. It is intentionally **doc-structure** coverage (paths, title, section headings, entry-point pointers)—not a duplicate of threat content, which remains authoritative in **[THREAT_MODEL.md](THREAT_MODEL.md)**.

### 6.1 Contract name

Use **`THREAT_MODEL doc linkage contract`** in test docstrings, assertion messages, and failure output so CI logs identify the obligation without reading stack frames.

### 6.2 Required markers (summary)

| Artifact | Requirement |
| -------- | ------------- |
| **`docs/THREAT_MODEL.md`** | Exists; first line **`# Threat Model: Checkpoint and State Data`**; contains the eight **`## …`** headings listed in the product backlog table above in **document order** (Builder: assert sequential occurrence so reordering or deletion fails). |
| **`README.md`** | Contains **`THREAT_MODEL.md`**. |
| **`docs/MISSION.md`** | Contains **`THREAT_MODEL.md`**. |

### 6.3 Refresh / drift-control rule

When maintainers **rename or move** **`docs/THREAT_MODEL.md`**, **change the document title line**, **renumber or drop** any of the eight section headings, or **remove** **`THREAT_MODEL.md`** mentions from **README** or **MISSION**:

1. Update **§6 and the product backlog table** in this file if the canonical markers change.
2. Update **`tests/test_threat_model_doc_linkage_contract.py`** (or the chosen module name) in the **same change set**.
3. If integrators or security reviewers would see a **materially different** security story (not just a path fix), add **`CHANGELOG.md` Unreleased** per **[CONTRIBUTING.md](CONTRIBUTING.md)** and **[docs/SECURITY_REPORTING_SPEC.md](SECURITY_REPORTING_SPEC.md)** as applicable.

**Anti-pattern:** Relaxing assertions to only “some markdown file exists” or dropping **MISSION** coverage—both entry points are **required** by the backlog.

### 6.4 Relationship to other contract tests

- **`tests/test_security_reporting_contract.py`** already requires **`THREAT_MODEL.md`** in root **`SECURITY.md`**; this backlog adds **README** / **MISSION** wiring and **THREAT_MODEL** structural anchors. Keep both modules **consistent** if the path to the threat model ever changes.
- This contract **does not** replace **replayt boundary** rules in §1–§3; it is **documentation integrity** only.
