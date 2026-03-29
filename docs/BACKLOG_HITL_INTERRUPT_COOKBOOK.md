# Backlog spec: Human-in-the-loop cookbook (`interrupt_before` / `interrupt_after`)

Normative **spec and acceptance criteria** for Mission Control backlog **Human-in-the-loop cookbook: interrupt_before / interrupt_after with tests** (item `4b64a655-bb06-49e5-8912-61b06626a034`). Phase **2** (spec lead) owns this document; phase **3** (builder) implements against it; phase **2b** (spec gate) checks completeness.

**Related normative docs:** checkpoint slice **[BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md](BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md)**; persistence and resume checklist **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** §6; public API **[API.md](API.md)** and **README**; assertion style **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)**.

---

## 1. Reconciliation with repository state

The following is **already true** in-tree unless a future change removes it:

- **`compile_replayt_workflow(..., interrupt_before=..., interrupt_after=...)`** forwards both kwargs to LangGraph **`StateGraph.compile`** for **`langgraph >=1.1.0,<1.2`** (see **`pyproject.toml`**).
- **`tests/test_bridge_graph.py`** includes **`test_resume_second_invoke_uses_memory_checkpointer`**, which uses **`interrupt_before=["second"]`** with **`MemorySaver`**, a stable **`thread_id`** in **`config["configurable"]`**, **`Runner`** + **`JSONLStore`**, and a second **`invoke(None, ...)`** — this satisfies a minimal **“at least one interrupt path”** bar for **`interrupt_before`** only.

**Documented gap this backlog closes:**

- README describes pause/resume in prose and points at §6 and the test above, but there is **no** dedicated **copy-paste** example that shows **`interrupt_before` / `interrupt_after` in the compile call** alongside **`MemorySaver`** and the two-**`invoke`** pattern (integrators must infer from the linear checkpoint snippet + paragraph).
- There is **no** automated test that exercises **`interrupt_after`**; both kwargs should be **CI-proven** if LangGraph semantics allow a small deterministic scenario.

---

## 2. User story (normative intent)

As an integrator building paused graphs, I need a **copy-paste path** that:

- Matches **LangGraph 1.1.x** **`invoke` / `config`** shapes used in CI (**`config={"configurable": {"thread_id": ...}}`**).
- Matches this bridge’s **Runner** wiring: **`context={"runner": runner}`** on **every** **`invoke`** for that thread, with a replayt **`Workflow`**, **`Runner`**, and store configured as in existing README examples.
- Shows how **`interrupt_before`** and **`interrupt_after`** use **replayt step names** (the same strings passed to **`@workflow.step("name")`** and **`note_transition`**), because the bridge maps those names to graph nodes.

---

## 3. Acceptance criteria (testable)

### 3.1 Documentation — cookbook quality (README and/or `docs/API.md`)

An integrator reading **published** docs (not **`src/`**) must find:

1. **Copy-paste Python** — At least one fenced example (single block or README + API with cross-links) that includes:
   - A minimal **two-step** **`Workflow`**, **`Runner`**, **`JSONLStore`** (or equivalent replayt store), and **`runner.run_id`** assignment **consistent with** the existing README checkpoint snippet.
   - **`compile_replayt_workflow(..., checkpointer=MemorySaver(), ...)`** with **`interrupt_before`** and/or **`interrupt_after`** as **lists of step name strings** (show at least **one** list non-empty; **prefer** showing **`interrupt_after`** explicitly if only one list is shown, so the doc matches the test obligation in §3.2).
   - First **`graph.invoke(initial_bridge_state(...), config=..., context={"runner": runner})`** and second **`graph.invoke(None, config=..., context={"runner": runner})`** with the **same** **`config`**, **`context`**, compiled graph, and saver.
   - A one-line clarification that **`interrupt_*`** values are **replayt** step names, forwarded to LangGraph **`compile`** (per **API.md**).

2. **Traceability** — Link to **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** §6 and name the canonical test module/function(s) that lock the example (e.g. **`test_resume_second_invoke_uses_memory_checkpointer`** plus any new **`interrupt_after`** test).

3. **`docs/API.md`** — If the full cookbook lives in README only, **API.md** must still retain (or add) a short **“see README — Human-in-the-loop”** (or equivalent) pointer so **API.md** readers discover the snippet; the existing **`interrupt_*`** forward to **`StateGraph.compile`** sentence stays authoritative for parameters.

### 3.2 Tests (`tests/test_bridge_graph.py` or adjacent module)

On the default CI install (**`uv sync --frozen --extra dev`**, **`uv run pytest`**, no **`demo`** extra, no network credentials):

1. **Keep** **`test_resume_second_invoke_uses_memory_checkpointer`** as the **`interrupt_before`** regression anchor.
2. **Add** at least **one** new test (or clearly scoped extension) that exercises **`interrupt_after`** with **`MemorySaver`**, the same **`Runner`** + **`thread_id`** resume pattern, and **replayt boundary** assertion messages per **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** (prefix **`replayt boundary:`** or equivalent contract naming). The test docstring must cite **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** §6 and this spec (**`BACKLOG_HITL_INTERRUPT_COOKBOOK.md`**) or the backlog item id.
3. **Assertions** must encode **observable** post-first-**`invoke`** state (e.g. **`replayt_next`**, **`context`** keys) consistent with **LangGraph 1.1.x** behavior for **`interrupt_after`** on the chosen step — derive expected values from current pinned LangGraph, not guesswork; adjust if upstream patch changes semantics.

**If** a maintainer discovers **`interrupt_after`** cannot be asserted deterministically on the supported stack, they must **not** silently drop coverage: document the blocker in a **spec gate** note, add an issue reference, and still ship §3.1 documentation for **`interrupt_after`** — this spec prefers **test + doc**; waiver requires explicit **2b** recorded decision.

### 3.3 `CHANGELOG.md`

When the builder lands user-visible cookbook text or clarifies **`interrupt_*`** semantics for integrators, add an **Unreleased** bullet per **CONTRIBUTING.md** / **RELEASE_CHANGELOG.md**. **Phase 2 (spec-only)** does not require a changelog entry.

---

## 4. Non-goals

- New public Python APIs (forwarding existing kwargs remains sufficient).
- First-class samples for every LangGraph saver backend (deferred per checkpoint slice).
- Product UX for human approvals beyond **compile-time interrupts + multi-`invoke` resume**.

---

## 5. Spec gate / builder checklist (phases 2b / 3)

- [ ] §3.1 copy-paste cookbook present in README and/or **API.md** with §3.1 traceability links.
- [ ] §3.2 **`interrupt_after`** test present and green on **Python** 3.11 and 3.12 CI (or explicit §3.2 waiver recorded in spec gate with issue link).
- [ ] Assertion messages remain contract-named per **REPLAYT_BOUNDARY_TESTS.md** for replayt-importing tests.
- [ ] **CHANGELOG.md — Unreleased** updated when integrator-facing doc/semantics ship.
