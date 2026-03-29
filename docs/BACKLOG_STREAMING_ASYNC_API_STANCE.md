# Backlog spec: Streaming / async API stance (LangGraph `astream` vs bridge guarantees)

Normative **spec and acceptance criteria** for Mission Control backlog **Streaming / async API stance: document LangGraph astream vs bridge guarantees** (item `1a4f20cb-d47f-433a-a1e8-2dca65a05417`). Phase **2** (spec lead) owns this document; phase **2b** (spec gate) checks completeness; phase **3** (builder) is **docs-only** for this item unless a follow-on adds code or tests.

**Related normative docs:** **[API.md](API.md)** (streaming subsection); **[README.md](../README.md)**; execution errors **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)**; checkpoints **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)**; inbound state **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**.

---

## 1. Reconciliation with repository state

| Topic | Current state |
| ----- | ------------- |
| **Compilation output** | `compile_replayt_workflow` returns a LangGraph **`CompiledStateGraph`** (typed as **`CompiledStateGraph`** in **`replayt_langgraph_bridge.graph`**). |
| **Node callables** | Bridge-registered graph nodes are **synchronous** Python functions that call replayt **`Workflow`** step handlers synchronously. |
| **CI / examples** | **`tests/`** and README examples exercise **`graph.invoke(...)`** with **`context={"runner": runner}`** (and checkpoint **`config`** where applicable). **No** automated coverage for **`stream`**, **`astream`**, **`ainvoke`**, **`batch`**, or **`abatch`**. |
| **Upstream API surface** | LangGraph documents **`stream`** / **`astream`**, stream modes (e.g. **`updates`**, **`values`**, **`messages`**, **`custom`**, **`checkpoints`**, **`tasks`**, **`debug`**), and **`version="v2"`** chunk shapes for LangGraph **≥ 1.1**. Async and Python **&lt; 3.11** caveats live in upstream docs. |

---

## 2. User story (normative intent)

As an **integrator** using LangGraph streaming or async entry points, I need the bridge docs to state **what is in scope**, **what is delegated to LangGraph**, and **what is explicitly not a bridge guarantee**, so I do not assume silent parity with the documented **`invoke`** cookbook or replayt **`Runner`** semantics.

---

## 3. Product acceptance criteria (verbatim backlog → testable IDs)

| ID | Source acceptance criterion | Normative interpretation |
| -- | --------------------------- | ------------------------- |
| **S1** | Add a concise subsection to **`docs/API.md`** (and a one-line README pointer) describing supported patterns today and referring to **LangGraph** upstream docs for anything not wrapped by the bridge. | **API.md** must include a dedicated section (stable heading for anchors — see §4.1) that: (i) names **synchronous `invoke`** as the **documented and CI-tested** integration path; (ii) states that **`stream`**, **`astream`**, **`ainvoke`**, and other **`CompiledStateGraph`** methods are **LangGraph runtime** APIs on the same compiled object; (iii) links to **official LangGraph** documentation for streaming modes, async usage, and **`RunnableConfig`** / Python-version caveats (minimum: **[LangGraph streaming (Python)](https://docs.langchain.com/oss/python/langgraph/streaming)**; optional: **[LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)** where checkpoint streaming is discussed). **README.md** must add **one** explicit markdown link to that **API.md** subsection (anchor text should mention **streaming** or **`astream`** / **`invoke`** contrast). |
| **S2** | If any behavior is explicitly unsupported, say so to prevent silent misuse. | **API.md** subsection must **explicitly** state that the bridge **does not** document, test, or extend LangGraph streaming semantics; **does not** treat per-chunk stream delivery as a separately guaranteed contract; and **does not** support **async** replayt step handlers or async-specific bridge wrappers. Integrators must not assume **`stream`/`astream`** timing or ordering matches all **`invoke`** mental models for **interrupts**, **checkpointers**, or **replayt store** side effects without consulting upstream behavior for their LangGraph version. |
| **S3** | Tests only if a code path is added; otherwise docs-only with **CHANGELOG** Unreleased if user-facing. | **No new tests** required for this backlog unless a later change adds bridge code paths for streaming. **CHANGELOG.md** — **Unreleased** — **Documentation** (or equivalent) must note integrator-visible **API.md** / **README** updates when those ship. |

---

## 4. Deliverable details (builder alignment)

### 4.1 Stable section heading (API.md)

Use this heading verbatim (slug stable for README links):

```markdown
## Streaming and async LangGraph entry points (`invoke`, `stream`, `astream`)
```

Expected GitHub-style fragment: `#streaming-and-async-langgraph-entry-points-invoke-stream-astream` (verify in renderer if linking from other surfaces).

### 4.2 Minimum content bullets (may be prose paragraphs)

1. **Supported / documented path** — Synchronous **`invoke`** with **`initial_bridge_state`**, optional **`config`** / **`checkpointer`**, and **`context={"runner": runner}`** as in README and **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)**; this is what maintainers test in CI.
2. **Upstream surface** — The same compiled graph exposes LangGraph’s **streaming and async** APIs; chunk formats, **`stream_mode`**, **`version`**, subgraph streaming, and async **`RunnableConfig`** behavior are **upstream-defined**.
3. **Bridge boundary** — Nodes run **sync** replayt handlers inside LangGraph’s scheduler; the bridge adds **no** streaming-specific adapters. **`messages`** mode and similar require **integrator** code (e.g. LangChain chat models inside handlers) that upstream can instrument—**not** a standalone bridge promise.
4. **Misuse guardrails** — Do not assume undocumented parity between **`invoke`** and **`astream`** for checkpoint edges, interrupt semantics, or replayt **`Runner`** / store observability without validating against LangGraph docs for the pinned **1.1.x** line.

### 4.3 Cross-spec index

Add a row to **`docs/API.md`** **Cross-spec index** pointing at this subsection for “streaming / async entry points”.

---

## 5. Non-goals (hard)

- **No new bridge APIs** or runtime wrappers for streaming unless a separate backlog says so.
- **No requirement** to add **`astream`** / **`stream`** tests in CI for this item alone.
- **No duplication** of full LangGraph streaming tutorials—link upstream instead.

---

## 6. Changelog policy

Integrator-visible **API.md** / **README** updates ship with **CHANGELOG.md — Unreleased — Documentation** per **CONTRIBUTING.md** / **RELEASE_CHANGELOG.md**.

---

## 7. Spec gate / builder checklist (phases 2b / 3)

- [ ] **S1** satisfied: **API.md** subsection + **README** one-line pointer with upstream link(s).
- [ ] **S2** satisfied: explicit **unsupported / undefined** language for bridge streaming guarantees and async handlers.
- [ ] **S3** satisfied: **CHANGELOG** **Unreleased** updated; **no** new tests unless code ships.
- [ ] **Cross-spec index** row in **API.md** updated.
- [ ] **This file** (`BACKLOG_STREAMING_ASYNC_API_STANCE.md`) linked from **API.md** backlog traceability or **Related** line if the project pattern calls for it (optional if index row cites streaming spec intent).
