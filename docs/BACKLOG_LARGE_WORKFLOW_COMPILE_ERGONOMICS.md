# Backlog spec: large-workflow compile ergonomics

Normative **spec and acceptance criteria** for Mission Control backlog **Large-workflow compile ergonomics: doc limits and optional warning hook** (item `d4f93fa1-214f-4740-a4c8-f7c9a78e4d86`). Phase **2** (spec lead) owns this document; phase **2b** (spec gate) checks completeness; phase **3** (builder) implements docs and optional code against it.

**Related:** Non-normative scale guidance and optional advisory rules live in **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)** (§5 and §4.3). Public entry point summary: **[API.md](API.md)**. Inbound dict limits (distinct from “how many steps”): **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**.

---

## 1. User story and problem

**Story:** As an integrator with many steps, I want **predictable compile-time behavior** and guidance before I hit pathological graphs.

**Problem today:** Graph construction **errors** are documented; **performance and size** expectations are easy to miss. Integrators may not know how step count maps to LangGraph wiring or where payload vs graph limits apply.

---

## 2. Scope

| In scope | Out of scope (unless a future backlog says otherwise) |
| -------- | ------------------------------------------------------ |
| **Documentation** — practical expectations for node/step counts, graph shape, and “deep nesting” disambiguation | Hard **enforced** maximum step count in the bridge |
| **Pointer** to integrator-owned profiling (`cProfile`, LangGraph docs, etc.) | Guarantees about compile-time latency on specific hardware |
| **Optional** advisory (`warnings.warn` or logger) at a **high** threshold, **opt-in** or **once per process**, plus a **small** test if implemented | Per-node spam, mandatory warnings on every compile, or new **failure** modes for large graphs |
| **`CHANGELOG.md`** when user-visible behavior ships (new flag, env var, or default warning policy) | Changing **STATE_PAYLOAD_VALIDATION** limits solely for this backlog |

**Docs-only delivery** is allowed: if phase **3** chooses not to implement an advisory, §3.2 and §4.3 in **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)** still define how a **later** advisory must behave.

---

## 3. Acceptance criteria (testable)

### 3.1 Documentation (required)

An integrator reading **only** published docs can find **non-normative** guidance that covers:

1. **Node / step count** — How many LangGraph nodes the bridge creates for **N** replayt steps, and that routing wiring is **dense** over step names (high-level; may reference `compile_replayt_workflow` / `graph.py` in maintainer-facing phrasing).
2. **Edges / routing** — That each step participates in conditional routing toward **all** declared steps and **`END`** (qualitative, not a formal big-O obligation).
3. **“Deep nesting”** — Clarify **control-flow** (flat nodes vs logical chain length) vs **`context`** nesting limits in **STATE_PAYLOAD_VALIDATION**.
4. **Profiling** — At least one concrete suggestion (e.g. stdlib **`cProfile`** or a named alternative) and a reminder to consult **LangGraph** docs for **`StateGraph.compile`** on the pinned line.

**Normative home:** **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)** §5. **Secondary pointer:** **[API.md](API.md)** (stable symbol table for `compile_replayt_workflow` and cross-spec index).

### 3.2 Optional advisory (if implemented)

If code emits a **large-graph** advisory:

1. **Mechanism** — `warnings.warn` and/or a **single** high-severity log line per advisory design (not per step).
2. **Noise policy** — **Either** **opt-in** (explicit parameter and/or environment variable, **default off**) **or** **once per process** for the same advisory (first threshold crossing only). **Forbidden:** default noisy repeated warnings on every compile in a long-lived process without integrator action.
3. **Semantics** — Advisory is **non-fatal**; compilation **succeeds** if the workflow is otherwise valid.
4. **Tests** — At least one **automated** test proving opt-in or once-per-process behavior; **`[dev]`** CI only; no **`demo`** extra; no network.
5. **Release hygiene** — **`CHANGELOG.md` — Unreleased** documents the switch and any integrator-visible default; warning **category** or log **message fragment** documented for those who filter logs.

Normative rules for that feature: **[GRAPH_CONSTRUCTION_ERRORS.md](GRAPH_CONSTRUCTION_ERRORS.md)** §4.3.

### 3.3 Changelog (when behavior changes)

Per project **[CONTRIBUTING.md](../CONTRIBUTING.md)** / **[RELEASE_CHANGELOG.md](RELEASE_CHANGELOG.md)** practice: any **user-visible** new parameter, environment variable, or default policy for advisories requires an **Unreleased** bullet in the **same** change set as the code. **Pure** doc clarifications under §3.1 may omit **CHANGELOG** unless maintainers treat them as notable for integrators.

---

## 4. Spec gate and builder checklist (phases 2b / 3)

- [ ] **GRAPH_CONSTRUCTION_ERRORS.md** §5 is present and labeled **non-normative**; links to **STATE_PAYLOAD_VALIDATION** for payload limits.
- [ ] **API.md** points integrators at **GRAPH_CONSTRUCTION_ERRORS** for scale/profiling (table and/or cross-spec index).
- [ ] If an advisory exists: §4.3 + §3.2 above satisfied; tests and **CHANGELOG** updated.
- [ ] If no advisory: backlog still **done** on docs alone; §4.3 remains the contract for **future** work.

---

## 5. Changelog policy

User-visible runtime or API surface from this backlog → **`CHANGELOG.md`**. Mission Control files under **`.orchestrator/`** stay out of git per repository policy.
