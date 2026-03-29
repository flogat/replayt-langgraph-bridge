# Backlog spec: LangGraph 1.2.x compatibility spike and pin-widen plan

Normative **spec and acceptance criteria** for Mission Control backlog **Compatibility spike: LangGraph 1.2.x API drift and pin widen plan** (item `ad68b829-7393-4455-8ecd-0c57fcd04cee`). Phase **2** (spec lead) owns this document; phase **3** (builder) runs the spike and lands code/docs; phase **2b** (spec gate) checks completeness.

**Related normative docs:** dependency policy **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** (**Rollout risk for LangGraph majors**, **Current dependency constraints**); lock and CI **[DEPENDENCY_LOCK_STRATEGY.md](DEPENDENCY_LOCK_STRATEGY.md)**; audit log **[DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md)**; checkpoint contract **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** §7; replayt-facing tests **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)**; public surface **[API.md](API.md)**; SQLite round-trip spec **[BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP.md](BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP.md)**.

---

## 1. Reconciliation with repository state

**Declared pin (today):** **`pyproject.toml`** requires **`langgraph>=1.1.0,<1.2`**. CI resolves the latest **1.1.x** line from **`uv.lock`** under **`[dev]`**.

**Problem:** Upstream **LangGraph 1.2.x** (pre-release, **main**, or stable when it ships) may change **compile-time types**, **checkpoint / saver** contracts, or **`invoke` / `config` / runtime `context=`** shapes. The bridge must not widen **`langgraph`**’s upper bound until maintainers understand **breaking deltas** and have a **shim or bump** story.

**Primary behavioral oracle (normative for this spike):** **`tests/test_bridge_graph.py`** — contract-style coverage for **`compile_replayt_workflow`**, **`MemorySaver`**, **`CompiledStateGraph.invoke(..., config=..., context=...)`**, **`interrupt_before` / `interrupt_after`**, and bridge errors (**`BridgeWorkflowCompileError`**, **`BridgeRoutingError`**, **`BridgeTransitionError`**). Any LangGraph change that breaks these tests without a deliberate bridge update is **API drift** for this backlog.

**Secondary oracle:** Disk checkpointer path **`tests/test_disk_checkpoint_sqlite_roundtrip.py`** (requires **`[dev]`** + **`langgraph-checkpoint-sqlite`**). The spike must **attempt** full **`uv run pytest`** (no path filter, same contract as CI). If the environment cannot collect that module, record the failure mode in the maintainer note and still complete **`test_bridge_graph`**-centric analysis.

---

## 2. LangGraph touchpoints to enumerate (inventory)

The Builder **must** diff or exercise the following **bridge-owned** integration surfaces against **1.1.x vs candidate 1.2.x**. Record **symbol / module path**, **1.1 behavior**, **1.2 behavior** (or **removed / moved**), and **impact** (none / type-only / runtime).

### 2.1 `compile_replayt_workflow` and graph build (`replayt_langgraph_bridge.graph`)

| Area | What to verify |
| ---- | ---------------- |
| **Imports** | **`langgraph.graph`**: **`END`**, **`START`**, **`StateGraph`**; **`langgraph.graph.state`**: **`CompiledStateGraph`**; **`langgraph.runtime`**: **`Runtime`**; **`langgraph.types`**: **`Checkpointer`**. |
| **Generics** | **`StateGraph[state, context, input, output]`** and **`CompiledStateGraph[...]`** parameter lists and variance — typing-only regressions matter for **`mypy -p replayt_langgraph_bridge`**. |
| **Compile kwargs** | **`StateGraph.compile(checkpointer=..., interrupt_before=..., interrupt_after=...)`** — keyword availability, types, and semantics (especially **interrupt** placement vs **1.1.x**). |
| **Node callable shape** | Step nodes use **`runtime: Runtime[ReplaytBridgeContext]`** and read **`runtime.context["runner"]`** — confirm **`Runtime`** / context injection API is unchanged or document migration. |
| **Routing** | **`add_conditional_edges`** + path map to **`END`** and step names — confirm routing API and **`END`** constant behavior. |

### 2.2 Checkpointer wrapping (`BridgeValidatingCheckpointSaver`)

| Area | What to verify |
| ---- | ---------------- |
| **Type of `checkpointer`** | **`Checkpointer | None`** accepted by **`compile_replayt_workflow`**; **`True` / `False`** sentinel handling before wrapping (see **`graph.py`**). |
| **Saver protocol** | **`BridgeValidatingCheckpointSaver`** delegates to upstream saver — any change to **`BaseCheckpointSaver`** method signatures, **`aget_tuple` / `put` / `list`**, or tuple shapes breaks validation or resume tests. |

### 2.3 Checkpoint base types (`replayt_langgraph_bridge.state_validation`)

| Area | What to verify |
| ---- | ---------------- |
| **Imports** | **`langgraph.checkpoint.base`**: **`BaseCheckpointSaver`**, **`Checkpoint`**, **`CheckpointMetadata`**, **`CheckpointTuple`**. |
| **RunnableConfig** | **`langchain_core.runnables.RunnableConfig`** usage at the validation boundary — confirm still compatible with LangGraph’s config channel. |

### 2.4 `invoke` / `config` / `context` (integrator-facing contract)

| Area | What to verify |
| ---- | ---------------- |
| **First / resume invoke** | **`graph.invoke(initial_bridge_state(...), config={"configurable": {"thread_id": ...}}, context={"runner": runner})`** and **`graph.invoke(None, config=..., context=...)`** — document any new required kwargs, renames, or deprecated aliases. |
| **Config shape** | **`config["configurable"]["thread_id"]`** and **`MemorySaver.list(config)`** — must remain coherent for **§7** patterns in **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)**. |
| **Runtime context** | Bridge **`ReplaytBridgeContext`** requires **`runner`**; confirm LangGraph still passes **`context=`** through to nodes unchanged. |

---

## 3. Spike procedure (time-boxed, branch-local)

1. **Branch** — Work on a throwaway or integration branch (e.g. **`mc/langgraph-1.2-spike`**); do not merge a pin widen without completing §4–§5.
2. **Candidate version** — Install **LangGraph 1.2.x** (pre-release wheel, **Git** URL, or **PyPI** when available). Record **exact** **`langgraph`**, **`langgraph-checkpoint`**, and related packages (**`langgraph-prebuilt`**, **`langgraph-sdk`**, etc.) in the maintainer note.
3. **Constraints** — Temporarily relax **`langgraph<1.2`** in **`pyproject.toml`** only on the spike branch; regenerate or override lock as needed for the experiment. **Production merge** must restore policy: either keep **`<1.2`** until §5 is satisfied or land a reviewed range bump + **`uv.lock`** + docs together.
4. **Commands** — Run **`uv run pytest`** (full suite, no path filter), **`uv run ruff check src tests`**, **`uv run mypy -p replayt_langgraph_bridge`** — same trio as **`.github/workflows/ci.yml`** job **`test`** (see **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** for pytest contract).
5. **Time box** — Cap wall-clock effort (e.g. **1–2 engineer-days**); partial enumeration is acceptable if the note lists **known unknowns** and follow-up issues.

---

## 4. Deliverable: maintainer note (where and what)

Publish **one** consolidated maintainer note that satisfies **all** rows in §4.1. Either:

- **A)** Add a dated subsection under **[DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md)** **History** (recommended for a short, durable log), **or**
- **B)** Open a **Compatibility Update** issue from **[`.github/ISSUE_TEMPLATE/compatibility_update.md`](../.github/ISSUE_TEMPLATE/compatibility_update.md)** and link it from **DEPENDENCY_AUDIT** and this spec.

### 4.1 Required content

| Section | Done when (normative) |
| ------- | ---------------------- |
| **Upstream versions** | Exact **`langgraph`** (and key transitive) versions exercised; date of spike. |
| **Breaking deltas** | Table or bullet list keyed by **§2** areas: **compile**, **checkpointer**, **invoke/config/context**, **checkpoint base** — each entry **breaking** / **compatible** / **unknown** with a one-line evidence pointer (test name, traceback, or upstream release note). |
| **Test signal** | **`pytest`** / **`mypy`** pass-fail summary; if failures, which tests and whether failures are **bridge** fixes vs **test expectation** updates (e.g. **`interrupt_after`** semantics). |
| **Shim strategy** | Recommended approach: e.g. **narrow code change** only, **`typing.TYPE_CHECKING`** / versioned imports, **runtime branch on `langgraph` version**, or **dual code path** with deprecation — pick one primary direction and list **non-options** (e.g. “no runtime dependency on unpublished internals”). |
| **Pin / SemVer decision** | Explicit recommendation: **widen** **`langgraph`** upper bound in a **semver-minor** bridge release vs **hold** **`<1.2`** until a follow-up vs **bridge major** — justify using **DESIGN_PRINCIPLES** **Rollout risk for LangGraph majors** and integrator impact. |

---

## 5. Acceptance criteria (testable)

### 5.1 Spike completeness

| ID | Criterion | Done when (normative) |
| --- | --------- | ---------------------- |
| **LG12-A1** | **Inventory** | Maintainer note covers every **§2** row (or marks **N/A** with reason). |
| **LG12-A2** | **Oracle** | Note references **`tests/test_bridge_graph.py`** outcomes explicitly (pass/fail/skip). |
| **LG12-A3** | **Automation** | Spike branch (or PR description) records **`pytest`**, **`ruff`**, **`mypy`** commands and exit codes. |
| **LG12-A4** | **Policy** | **§4.1 Pin / SemVer decision** is stated; if widening, **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** **Current dependency constraints** and **`README.md`** compatibility lines are updated **in the same change set** as **`pyproject.toml`** / **`uv.lock`** (builder phase — not required for phase **2** spec-only). |

### 5.2 Documentation alignment (post–pin change)

When the Builder **widens** **`langgraph`** (not required for the spike note alone):

| ID | Criterion | Done when (normative) |
| --- | --------- | ---------------------- |
| **LG12-A5** | **CHANGELOG** | **`CHANGELOG.md`** **Unreleased** documents integrator-visible range change per **[RELEASE_CHANGELOG.md](RELEASE_CHANGELOG.md)**. |
| **LG12-A6** | **Checkpoint docs** | If **`invoke`** or interrupt semantics change for integrators, **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** §7 and **[API.md](API.md)** gain matching updates. |

---

## 6. Non-goals (hard)

- **Not** committing a long-lived **`langgraph`** widen **without** CI-green **`[dev]`** lockfile and the maintainer note (**§4**).
- **Not** scope-expanding to **async** / **streaming** first-class support — see **[BACKLOG_STREAMING_ASYNC_API_STANCE.md](BACKLOG_STREAMING_ASYNC_API_STANCE.md)**; this spike may **mention** drift there but does not require implementation.
- **Not** changing **replayt** pins as part of this backlog unless a **documented** transitive conflict forces it (separate compatibility decision).

---

## 7. Spec gate / builder checklist (phases 2b / 3)

- [ ] **§3** spike procedure executed on a branch; versions recorded.
- [ ] **§4** maintainer note landed (**DEPENDENCY_AUDIT** and/or **Compatibility Update** issue + links).
- [ ] **`tests/test_bridge_graph.py`** green on candidate **1.2.x** after any bridge shims, or failures triaged with explicit **LG12** follow-ups.
- [ ] If pin widens: **`pyproject.toml`**, **`uv.lock`**, **README**, **DESIGN_PRINCIPLES**, **CHANGELOG** — **LG12-A4**–**A6**.
- [ ] **`tests/test_dependency_strategy.py`** (or successor) still reflects declared **`langgraph`** range if contract tests encode it.

---

## 8. Related documents

- **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** — **Rollout risk for LangGraph majors**; **Breaking upstream releases — triage**.
- **[DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md)** — vulnerability and **History**; target for **§4** note.
- **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** — **§7** **`MemorySaver`** / **`thread_id`** patterns exercised by **`test_bridge_graph.py`**.
