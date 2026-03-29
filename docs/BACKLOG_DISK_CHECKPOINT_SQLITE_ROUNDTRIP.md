# Backlog spec: Optional disk-backed checkpoint round-trip (SQLite)

Normative **spec and acceptance criteria** for Mission Control backlog **Add optional disk-backed checkpoint round-trip test (SQLite)** (item `255db7a8-876d-475d-8c69-cdb5f0c9fcc0`). Phase **2** (spec lead) owns this document; phase **3** (builder) implements against it; phase **2b** (spec gate) checks completeness.

**Related normative docs:** checkpoint slice **[BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md](BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md)** (previously deferred an in-repo disk round-trip); persistence contract **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** §3–§7; inbound validation **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**; replayt-facing assertion style **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)**; public entry points **[API.md](API.md)** and **README**.

---

## 1. Reconciliation with repository state

**Already satisfied (must remain green):**

- **[BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md](BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md) §3.2** — at least one **non-network**, **in-process** checkpointer path (**`MemorySaver`**) on the default CI install, with resume coverage in **`tests/test_bridge_graph.py`** and validation-adjacent tests in **`tests/test_state_payload_validation.py`**.

**Gap (this backlog):** There is **no** automated proof that a **durable** (disk-backed) LangGraph checkpointer survives a boundary where the **in-memory graph object** or **Python process** is not assumed to stay alive—only that **`MemorySaver`** works inside one process. Integrators choosing **SQLite** or other file-backed savers need **CI-visible** evidence that the bridge’s **`invoke`** / **`thread_id`** / **`context={"runner": runner}`** pattern interoperates with upstream disk serialization for the pinned **langgraph 1.1.x** line.

**Dependency reality (as of spec time):** Root **`uv.lock`** for **`uv sync --frozen --extra dev`** resolves **`langgraph`** and **`langgraph-checkpoint`** but **does not** include a SQLite saver distribution. Upstream ships **`langgraph-checkpoint-sqlite`** (PyPI) as the common **SQLite** implementation; the Builder must add a **version compatible** with the locked **`langgraph-checkpoint`** line, declare it under **`[project.optional-dependencies] dev`** with a short comment, and **regenerate **`uv.lock`**** so default CI installs it. If maintainers prefer a different **non-network disk-backed** saver documented for the same LangGraph line, this spec still applies **mutatis mutandis** (filesystem store, same proof obligations)—but the backlog title names **SQLite** as the **primary** target.

---

## 2. User story (normative intent)

As a **maintainer**, I need a **focused pytest** that:

1. Uses a **non-network** LangGraph **`Checkpointer`** that **persists to disk** ( **`SQLite` file in a temporary path** preferred).
2. Proves **checkpoint bytes survive** at least **one** meaningful boundary **where feasible**—for example:
   - **Process boundary:** first run writes checkpoints under **`subprocess`** or equivalent fresh interpreter; second run **reopens** the same DB path and **resumes** the same **`thread_id`**; **or**
   - **Compile boundary:** two separate **`compile_replayt_workflow(..., checkpointer=...)`** calls (or two **`CompiledStateGraph`** instances) backed by the **same on-disk saver** and **`thread_id`**, demonstrating load after **new compilation** in the same process.
3. Documents **platform / environment constraints** (temp directory behavior, SQLite file locking on Windows vs Linux CI, single-threaded test assumptions, **no** concurrent writers).

As an **integrator**, I can read **CHECKPOINT_PERSISTENCE.md** and **this backlog** to see that disk-backed savers are **exercised in CI**, not only described.

---

## 3. Acceptance criteria (testable)

### 3.1 CI and dependency surface

| Criterion | Done when (normative) |
| --------- | ---------------------- |
| **Default CI** | The test is collected and passes under **`.github/workflows/ci.yml`** job **`test`**: **`uv sync --frozen --extra dev`** then **`uv run pytest`** with **no path or marker filter** (same contract as **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** and **README** / **CONTRIBUTING**). |
| **No `demo` extra** | The scenario does **not** require **`replayt-langgraph-bridge[demo]`** or live vendor LLM clients. |
| **No network credentials** | No cloud checkpoint backends, no HTTP APIs, no outbound network **required** for the assertion path. |
| **Lockfile truth** | Any new distribution needed for the saver (e.g. **`langgraph-checkpoint-sqlite`**) appears in **`uv.lock`** after **`uv lock`** (or the project’s documented lock refresh), with a **commented** entry under **`[project.optional-dependencies] dev`** explaining it is for **disk checkpoint CI coverage** (not the default **`pip install replayt-langgraph-bridge`** surface). |

### 3.2 Scenario depth (minimum bar)

| Criterion | Done when (normative) |
| --------- | ---------------------- |
| **Disk persistence** | Checkpoints are written to a **real filesystem path** (temporary directory under **`tmp_path`** or **`tempfile`**) using a **SQLite**-backed saver **or** an equivalent upstream-documented disk backend if SQLite is blocked by a compatibility issue **documented in the test module docstring and spec gate**. |
| **Bridge wiring** | Uses **`compile_replayt_workflow`** with that checkpointer, **`invoke`** with **`context={"runner": runner}`**, and stable **`config["configurable"]["thread_id"]`** (same shape as existing **`MemorySaver`** tests). |
| **Replayt store** | Uses a **real** **`replayt`** **`Runner`** and a **local** durable or in-memory replayt store appropriate to the scenario (e.g. **`JSONLStore`** to a temp file) so **both persistence planes** stay coherent with **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** — graph checkpoint on disk **and** replayt run records where the scenario needs them. |
| **Boundary proof** | At least **one** of: **(A)** cross-process resume, **(B)** second **`compile_replayt_workflow`** + resume on same DB, per §2.2. If **(A)** is impractical in CI (flaky or slow), **(B)** must be implemented and the docstring must state why **(A)** was skipped. |
| **Determinism** | No wall-clock races; assertions use stable workflow definitions (same pattern as **`tests/test_bridge_graph.py`**). |

### 3.3 Assertions and traceability

| Criterion | Done when (normative) |
| --------- | ---------------------- |
| **REPLAYT_BOUNDARY_TESTS** | Any assertion that guards **replayt** behavior (**`Workflow`**, **`Runner`**, **`RunContext`**, store) uses **contract-named** messages (`replayt boundary: …`, **`pytest.raises(..., match=…)`**, or the two-argument **`assert`** form) per **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** §2–§3. |
| **Checkpoint docstrings** | Module or test docstring references **`docs/CHECKPOINT_PERSISTENCE.md`** §7 and **`docs/BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP.md`** (this file). |
| **Platform notes** | **`CHECKPOINT_PERSISTENCE.md`** §3 or §7 gains a short **“Disk-backed tests (CI)”** paragraph **or** the test module docstring (duplicated in §8 **Related documents** pointer) lists: supported OS assumptions (Linux CI primary; Windows/WSL caveats if any), SQLite temp-file cleanup, and **single-threaded** test scope. |

### 3.4 Changelog

| Criterion | Done when (normative) |
| --------- | ---------------------- |
| **Unreleased** | **`CHANGELOG.md`** gains an **Unreleased** bullet when the Builder lands **dependencies** (new **`dev`** package), **new public behavior**, or **integrator-visible doc** changes. **Pure** test addition with **dev-only** dependency still warrants a **Documentation** or **Added** note per **[CONTRIBUTING.md](CONTRIBUTING.md)** so release notes mention **SQLite / disk checkpoint CI coverage**. No **Unreleased** entry is required for **this phase-2 spec file alone**. |

---

## 4. Non-goals (hard)

- **Not** an exhaustive matrix of every LangGraph disk backend (Postgres, cloud)—only **one** focused **SQLite** (or documented fallback) path.
- **Not** a new bridge API or default checkpointer implementation.
- **Not** load testing, corruption injection, or multi-tenant isolation proofs (**[HOSTED_DEPLOYMENT_AUTHZ.md](HOSTED_DEPLOYMENT_AUTHZ.md)** remains normative for production topology).

---

## 5. Spec gate / builder checklist (phases 2b / 3)

- [ ] **`langgraph-checkpoint-sqlite`** (or chosen disk saver) declared under **`dev`** with **`pyproject.toml`** comment; **`uv.lock`** regenerated; CI **`test`** job stays **`[dev]`**-only.
- [ ] New **`tests/`** module (or clearly scoped tests in an existing module) implements §3.2 with §3.1 constraints.
- [ ] §3.3 traceability and platform notes satisfied.
- [ ] **`docs/CHECKPOINT_PERSISTENCE.md`** §7 disk bullet checked off; **README** optional one-line pointer if maintainers want discoverability (not mandatory if **CHECKPOINT_PERSISTENCE** §7 is sufficient).
- [ ] **`CHANGELOG.md` — Unreleased** updated per §3.4 when implementation merges.
