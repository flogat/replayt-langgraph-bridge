# Backlog spec: Replayt 0.5 readiness checklist and boundary test updates

Normative **spec and acceptance criteria** for Mission Control backlog **Replayt 0.5 readiness checklist and boundary test updates** (item `8c5e0a89-66d8-4e11-ac7e-532b39f11156`). Phase **2** (spec lead) owns this document; phase **3** (builder) implements against it; phase **2b** (spec gate) checks completeness.

**Ecosystem stance:** Consumer-side pins, shims, tests, and docs live **in this repository** per **[REPLAYT_ECOSYSTEM_IDEA.md](REPLAYT_ECOSYSTEM_IDEA.md)**.

**Related normative docs:** **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md#breaking-upstream-releases--triage)** (triage, pins); **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** (§1 symbol table, actionable messages, backlog mapping); issue template **[`.github/ISSUE_TEMPLATE/compatibility_update.md`](../.github/ISSUE_TEMPLATE/compatibility_update.md)**; draft issue body **[COMPATIBILITY_UPDATE_REPLAYT_05.md](COMPATIBILITY_UPDATE_REPLAYT_05.md)**; **[CONTRIBUTING.md](../CONTRIBUTING.md)**; **`pyproject.toml`**; **`uv.lock`** / **[DEPENDENCY_LOCK_STRATEGY.md](DEPENDENCY_LOCK_STRATEGY.md)**.

---

## 1. Reconciliation with repository state

Treat the following as **facts** for builders unless a later change explicitly updates this section:

| Topic | Current state |
| ----- | ------------- |
| **`replayt` pin** | **`>=0.4.0,<0.5`** in **`pyproject.toml`** — blocks silent install of **0.5.x** until this backlog (or a successor) completes the readiness path. |
| **Bridge `src/` imports** | **`replayt.runner`**: `RunContext`, `Runner`; **`replayt.workflow`**: `Workflow` (see **`src/replayt_langgraph_bridge/graph.py`**). Docstrings reference replayt types elsewhere; no other **`replayt.*`** runtime imports in **`src/`** today. |
| **Tests importing replayt** | Multiple modules under **`tests/`** import **`replayt.workflow`**, **`replayt.runner`**, **`replayt.persistence`** (e.g. **`JSONLStore`**), and **`tests/test_replayt_boundary_contracts.py`** imports **`replayt`** at package level — see ripgrep / **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md) §1**. |
| **Normative boundary symbol table** | **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md) §1** lists **supported** replayt entry points the bridge relies on. If **0.5** requires new public APIs, **§1** and any contract tests must be updated **together** (same change set). |
| **CI contract** | **`.github/workflows/ci.yml`** job **`test`**: **`uv sync --frozen --extra dev`**, then **`uv run pytest`** with **no path/marker filter**, **ruff**, **mypy** — same as other compatibility backlogs. |

**Inventory procedure (required before pin widen):**

1. List every **`from replayt…`** / **`import replayt`** in **`src/replayt_langgraph_bridge/`** and in **`tests/`** files that are **replayt boundary** or **persistence** scenarios (not mocks-only).
2. For each symbol, record whether it is **documented public** replayt API (release notes, `__all__`, or upstream docs) or a **compatibility risk** if non-public.
3. Compare against **replayt 0.5** (prerelease or GA) **release notes** and **deprecation** notices; paste summary into the **Compatibility Update** issue body (**§2 R1**).

---

## 2. Product acceptance criteria (verbatim backlog → testable IDs)

| ID | Source intent | Done when (normative) |
| -- | ------------- | ---------------------- |
| **R1** | **Compatibility Update** issue filled out | A **GitHub Compatibility Update** issue exists (new or updated) from **[`.github/ISSUE_TEMPLATE/compatibility_update.md`](../.github/ISSUE_TEMPLATE/compatibility_update.md)** with **Package name** **replayt**, **New version** set to the **0.5** line under test (prerelease tag or GA). **Test Results**, **Impact Assessment**, and **Required Changes** sections are filled (not placeholders). The issue body includes the **Replayt 0.5+ compatibility** checklist from the template (or equivalent bullets) and links **this document**. |
| **R2** | Track **public API** vs **imports** in **`src/`** and contract tests | The same issue (or an appendix comment on it) contains an **API inventory** table or bullet list: each **`replayt.*`** symbol used in **`src/`** and in boundary-style **`tests/`** modules, marked **still valid / renamed / removed / replaced** for the target **0.5** version. If the bridge must depend on a **new** replayt symbol, that symbol is listed and justified as **public** upstream API. |
| **R3** | **`pyproject` pin decision** | **Decision recorded in the issue** and reflected in **`pyproject.toml`** when the implementation merges: e.g. raise floor to **`>=0.5.0`** and upper bound to **`<0.6`** (pattern mirrors current **0.4.x** line), **or** keep **`<0.5`** until blockers clear, **or** document a **time-boxed** branch-only experiment — in all cases with **maintainer rationale** tied to **R4** outcomes. Final **`pyproject.toml`** comments must justify the chosen range per **DESIGN_PRINCIPLES** *Justifying new or changed runtime constraints*. |
| **R4** | **Green CI on prerelease** **or** **documented blockers** | **Either** (A) a **CI run** (prefer **GitHub Actions** on a PR branch, or pasted local matrix) shows **`uv sync --frozen --extra dev`** (or equivalent documented override only if lock cannot yet pin **0.5**) and **`uv run pytest`** **green** on **Python 3.11, 3.12, and 3.13** with the candidate **replayt** version, **or** (B) the **Compatibility Update** issue lists **upstream blockers** with **URLs** (issues/PRs/changelog) and states what the bridge is **waiting on** — sufficient for maintainers to reopen the work; **chat-only** blockers are **not** sufficient. |
| **R5** | **Extend `REPLAYT_BOUNDARY_TESTS` acceptance mapping** | If **0.5** introduces **new** replayt surfaces the bridge **must** exercise in contract tests, **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** gains: (i) an updated **§1** table row(s) for those symbols; (ii) the **product backlog mapping** row for **this** Mission Control item (§ in that file); (iii) **Related documents** link to **this** spec. If **no** new surfaces are required, the issue **explicitly** states “§1 unchanged” with one-line justification. |

---

## 3. Builder checklist (phase 3 / gate)

- [ ] **R1** — Compatibility issue filed/updated; template sections complete; link to **this doc**.
- [ ] **R2** — API inventory for **`src/`** + contract **`tests/`** vs **replayt 0.5**; public vs risk called out.
- [ ] **R3** — **`pyproject.toml`** range matches recorded decision; **DESIGN_PRINCIPLES** *Current dependency constraints* and **README** compatibility lines updated when integrator-facing ranges change.
- [ ] **R4** — Green CI matrix evidence **or** blocker list with upstream links in the issue.
- [ ] **R5** — **REPLAYT_BOUNDARY_TESTS.md** updated per above, or “§1 unchanged” documented in the issue.
- [ ] **`uv.lock`** — Regenerated (or justified) when **`pyproject.toml`** / resolution changes; **`uv sync --frozen --extra dev`** succeeds on CI.
- [ ] **CHANGELOG.md** — **Unreleased** when **R3** changes published dependency ranges (per **CONTRIBUTING.md**).
- [ ] **Code / tests** — Shims or test updates as needed so the suite matches the new contract (out of scope for phase **2** spec-only work).

---

## 4. Explicit non-goals (this backlog)

- **LangGraph** major/minor widens (**1.2+**, etc.) — use **[BACKLOG_LANGGRAPH_12_COMPATIBILITY_SPIKE.md](BACKLOG_LANGGRAPH_12_COMPATIBILITY_SPIKE.md)** and the general **Compatibility Update** flow.
- **New bridge public API** solely for convenience — only when **replayt 0.5** forces integrator-visible behavior or typing changes; otherwise prefer internal shims.
- **Forking or vendoring replayt** — remains upstream’s scope per ecosystem doc.

---

## 5. Spec gate (phase 2b)

- [ ] **R1–R5** are unambiguous and traceable from **this doc** + **compatibility_update.md** + **REPLAYT_BOUNDARY_TESTS.md**.
- [ ] Pin story in **`pyproject.toml`**, **DESIGN_PRINCIPLES**, and **README** stays consistent after implementation.
- [ ] No silent widening of **`replayt`** range without **R2** inventory and **R4** green-or-blockers evidence.
