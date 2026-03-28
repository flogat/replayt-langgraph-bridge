# Backlog spec: LangGraph checkpoint integration slice

Normative **spec and acceptance criteria** for Mission Control backlog **Add LangGraph checkpoint integration slice** (item `6e2e8723-57c1-4f0c-bb74-6e9eb10beb23`). Phase **2** (spec lead) owns this document; phase **3** (builder) implements or verifies against it; phase **2b** (spec gate) checks completeness.

**Related normative docs:** persistence contract **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)**; inbound state and wrapped saver **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**; hosted backends **[HOSTED_DEPLOYMENT_AUTHZ.md](HOSTED_DEPLOYMENT_AUTHZ.md)**; public entry points **[API.md](API.md)** and **README**.

---

## 1. Reconciliation with repository state

Kickoff text for this backlog sometimes claims that checkpoints are promised but **not implemented**. That is **stale** for this repository: the bridge already compiles with an optional LangGraph **`Checkpointer`**, wraps it for inbound validation, and ships tests that use **`MemorySaver`** without network credentials.

**Builders must treat the following as the authoritative baseline** unless a future change explicitly removes it:

- **`compile_replayt_workflow(..., checkpointer=..., interrupt_before=..., interrupt_after=...)`** — forwards to LangGraph **`StateGraph.compile`** for **langgraph `>=1.1.0,<1.2`** (see **`pyproject.toml`**).
- **Deterministic tests** on the default **`pip install -e ".[dev]"`** / CI path: **`tests/test_bridge_graph.py`** (including **`test_resume_second_invoke_uses_memory_checkpointer`**), **`tests/test_state_payload_validation.py`**. Tests should keep docstring traceability to **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** §6 per **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)**.

Work under this backlog is therefore **primarily verification, documentation clarity, and gap closure**—not a greenfield checkpoint feature—unless scope is explicitly widened below.

---

## 2. First slice: in scope vs deferred

| In scope for this slice | Explicitly deferred (later backlogs) |
| ----------------------- | -------------------------------------- |
| Integrator passes a LangGraph **1.1.x**-compatible **`Checkpointer`** into **`compile_replayt_workflow`** | Bridge-shipped **default** durable backend or encryption |
| **In-process** checkpoint round-trip (e.g. **`MemorySaver`**) for docs, CI, and local debugging | **Distributed** coordination, multi-tenant isolation guarantees |
| **Resume** semantics: multiple **`invoke`** calls with the same **`thread_id`** (via **`config["configurable"]`**) and the same compiled graph + saver, including **`interrupt_before` / `interrupt_after`** where needed | In-repo **first-class** samples for every upstream saver (SQLite, Postgres, cloud); integrators follow **LangGraph / langgraph-checkpoint** docs until a backlog adds maintained examples |
| **Limitations** documented: ephemeral vs durable vs hosted (**CHECKPOINT_PERSISTENCE.md** §2–3; **HOSTED_DEPLOYMENT_AUTHZ.md**) | Equating LangGraph checkpoint durability with **replayt** **Runner** / **store** durability (separate ownership; see **CHECKPOINT_PERSISTENCE.md** §1) |

---

## 3. Acceptance criteria (testable)

### 3.1 Documented API or usage path

An integrator reading **only** published docs (not **`src/`**) can:

1. See how to pass **`checkpointer=`** and run **`invoke`** with a **`thread_id`** for **LangGraph 1.1.x**.
2. Find the normative persistence and limitation story in **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** and the **`interrupt_*`** note in **[API.md](API.md)**.

**Minimum bar:** **README** includes a **checkpoint-enabled** example (e.g. **`MemorySaver`** + **`config={"configurable": {"thread_id": ...}}`** + **`context={"runner": runner}`**) distinct from the minimal no-checkpointer snippet.

### 3.2 Tests without network credentials

At least **one** automated test path proves **save/load or resume** with a **non-network** checkpointer on the **`[dev]`**-only CI install. **Current baseline:** tests listed in §1; regressions must stay fixed or replaced with equivalent coverage.

Assertion failures should remain **contract-named** where **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** applies (replayt imports).

### 3.3 Limitations (single-process vs distributed)

Docs explicitly state:

- **Ephemeral / single-process** patterns (**MemorySaver**-class) vs **durable** backends and **hosted** deployments.
- That the bridge does **not** implement distributed or production-grade storage by itself.

**Normative home:** **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** §2–3; **hosted** controls in **[HOSTED_DEPLOYMENT_AUTHZ.md](HOSTED_DEPLOYMENT_AUTHZ.md)**.

---

## 4. Spec gate and builder checklist (phase 2b / 3)

- [x] **README** checkpoint example matches **LangGraph 1.1.x** **`invoke`** / **`config`** shape maintained in **`tests/test_bridge_graph.py`** (update docs if upstream renames keys). _(Verified phase **3**.)_
- [x] **`compile_replayt_workflow`** signature and behavior match **[API.md](API.md)** and **README** Public API bullets. _(Verified phase **3**.)_
- [x] §3 acceptance criteria remain satisfied after any code change; if **SQLite** (or other disk) round-trip becomes a **new** requirement, add tests + **CHANGELOG** under **Unreleased** and extend §2 “in scope” explicitly. _(No disk round-trip required for this slice; criteria satisfied phase **3**.)_

---

## 5. Changelog policy

User-visible doc changes from closing this backlog (new examples, revised checkpoint guidance) belong under **CHANGELOG.md — Unreleased** per **CONTRIBUTING.md**. Pure internal Mission Control text under **`.orchestrator/`** is not versioned in git.
