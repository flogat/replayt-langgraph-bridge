# Backlog spec: SemVer signaling and automated public export alignment (`__all__` ↔ `API.md`)

Normative **spec and acceptance criteria** for Mission Control backlog **Release engineering: semver and API.md export set automation** (item `3dfb93e5-dbbd-42f6-bf63-16292e678884`). Phase **2** (spec lead) owns this document; phase **3** (builder) implements checks and doc touch-ups; phase **2b** (spec gate) checks completeness.

**Related normative docs:** canonical export rules **[API.md](API.md)**; SemVer, changelog, and release process **[RELEASE_CHANGELOG.md](RELEASE_CHANGELOG.md)**; contributor changelog rules **[CONTRIBUTING.md](../CONTRIBUTING.md)**; CI parity **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** and **`.github/workflows/ci.yml`**.

---

## 1. Reconciliation with repository state

| Topic | Current state |
| ----- | --------------- |
| **Canonical runtime list** | `replayt_langgraph_bridge.__all__` in **`src/replayt_langgraph_bridge/__init__.py`**. |
| **Normative doc list** | **Stable public symbols** table (first column **`Symbol`**) in **[API.md](API.md)** § **Stable public symbols (integrator-facing)**. |
| **README** | **[README.md](../README.md)** states supported names are **exactly** those in **`__all__`**; the bullet **Summary** is narrative and **must not** contradict the canonical set (it does not need to enumerate every symbol if it defers to **`__all__`** / **API.md**). |
| **Automation today** | Default **`pytest`** (including CI job **`test`**, **`uv run pytest`** with no path filter) runs **`tests/test_public_api.py`** **`test_all_matches_docs_api_stable_table`**, which parses the **Stable public symbols** table per **E2** and requires set equality with **`replayt_langgraph_bridge.__all__`**; failures list **`only_in_all`** and **`only_in_api_md`** (**E3**). |
| **Changelog / SemVer** | **[RELEASE_CHANGELOG.md](RELEASE_CHANGELOG.md)** defines **MAJOR** / **MINOR** / **PATCH** and **Breaking** / **Experimental** lead-ins; phase **2** adds explicit **public export set** bump guidance in that doc (§ **Public export set and SemVer**). |

---

## 2. Problem statement (operator)

Downstream pins (`~=0.1`, upper bounds, lockfiles) assume **API.md** and **`__all__`** stay aligned. Silent drift (code exports a name not in **API.md**, or docs promise a symbol not in **`__all__`**) breaks integrator trust. Release bumps should be **predictable**: export additions vs removals map cleanly to **MINOR** vs **Breaking** / **MAJOR** expectations per **[RELEASE_CHANGELOG.md](RELEASE_CHANGELOG.md)**.

---

## 3. Product acceptance criteria (testable IDs)

| ID | Requirement | Verification |
| -- | ------------- | ------------ |
| **E1** | **Automated alignment check** — A **lightweight** check (pytest test module, small stdlib script invoked from pytest, or equivalent) fails when the set of names in **`replayt_langgraph_bridge.__all__`** (after import under **`[dev]`** install, same as CI) **differs** from the set of **stable public symbols** parsed from **API.md**. | **`uv run pytest`** on the default CI matrix (**no** path filter that skips this test) fails on intentional drift; passes on aligned trees. |
| **E2** | **Parsing rules (normative)** — The expected symbol set is derived **only** from **[API.md](API.md)** heading **`## Stable public symbols (integrator-facing)`** and its **markdown table**: each **data** row’s **first column** contributes **exactly one** symbol name, taken from a single **inline code** span (backticks) containing the identifier (e.g. `` `compile_replayt_workflow` ``). Ignore the header row and markdown separator row. **Do not** harvest symbols from prose outside that table for this check. | Code comment or docstring in the test/helper cites this section ID **E2**; a maintainer can add a table row and matching **`__all__`** entry without changing parser logic beyond normal table rows. |
| **E3** | **Failure messages** — On mismatch, the failure output **lists** `only_in_all`, `only_in_api_md` (or equivalent), and **names the contract** (e.g. **public export set** / **API.md stable table** / **`__all__`**) so contributors fix **API.md**, **`__init__.py`**, or both without guessing. | Assertion message / `pytest` output is copy-paste friendly; aligns with assertion style expectations in **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** where applicable (contract named, not only deep equality). |
| **E4** | **No extra runtime deps** — The check uses the **existing** **`[dev]`** toolchain (stdlib + **pytest** + whatever the repo already uses for doc contract tests). **Do not** add a heavy doc toolchain solely for this backlog unless the project already standardizes on it elsewhere. | **`pyproject.toml`** / **`uv.lock`** unchanged **or** only touched if the project chooses an existing shared parser already required by other tests. |
| **E5** | **CI parity** — The check runs in the primary **`test`** job (same **`uv sync --frozen --extra dev`** path as **[`.github/workflows/ci.yml`](../.github/workflows/ci.yml)**). | Workflow diff not required if the new test is collected by default **`pytest`**; if a separate job is added, **README** / **CONTRIBUTING** / **REPLAYT_BOUNDARY_TESTS** must mention it (prefer default **`pytest`**). |
| **E6** | **RELEASE_CHANGELOG.md** — Document how **public export set** changes map to **SemVer** and **CHANGELOG.md** entries (see **[RELEASE_CHANGELOG.md](RELEASE_CHANGELOG.md) — Public export set and SemVer**). | Section present and consistent with §3 **MAJOR** / **MINOR** / **PATCH**; references **API.md** and **`__all__`**. |
| **E7** | **CONTRIBUTING.md** — Short bullet under **changelog** (or **public API**) pointing maintainers at: (1) **E6** when editing **`__all__`**, (2) the new test when **`__all__`** or the **API.md** stable table changes. | Link to **RELEASE_CHANGELOG.md** anchor and **API.md**; optional link to this backlog doc. |
| **E8** | **API.md** — Cross-link this backlog from **Cross-spec index** (and optionally **Source of truth for exported names**) so builders know the **E1** check exists after phase **3**. | Anchor row in **Cross-spec index**; **Source of truth** bullet mentions automated check once implemented. |

### 3.1 Optional stretch (not required to close the backlog)

| ID | Requirement |
| -- | ------------- |
| **E9 (optional)** | **Changelog co-change heuristic** — If the project wants stricter guardrails: a CI step or test that uses **`git`** to assert any commit touching **`__init__.py`**’s **`__all__`** literal also touches **`CHANGELOG.md`** **Unreleased**. This is **brittle** for multi-commit PRs and **optional**; normative bar remains **E1**–**E8**. |

---

## 4. SemVer and changelog expectations (summary for builders)

Normative detail lives in **[RELEASE_CHANGELOG.md](RELEASE_CHANGELOG.md)** after phase **2** edits. Summary:

- **Add** a name to **`__all__`** and the **API.md** table → typically **MINOR** (or **Added** under **Unreleased**); on **0.x**, still document under **Unreleased** before release.
- **Remove** or **rename** a stable symbol → **Breaking** lead-in and **[API.md](API.md)** / migration notes; **MAJOR** after **1.0**; **0.x** uses explicit **Breaking** / **Removed** per **RELEASE_CHANGELOG** §2–§3.
- **Reorder** only **`__all__`** (same set) → **PATCH** or omitted if trivial and no integrator-visible story (still must pass **E1**).
- **Doc-only** fixes to **API.md** prose (table unchanged) → **PATCH** / **Documentation** as usual.

---

## 5. Changelog for phase 3 (builder)

When the **automated check** and any **CONTRIBUTING** / **workflow** edits land, add **CHANGELOG.md** **Unreleased** bullets per **[CONTRIBUTING.md](../CONTRIBUTING.md)** (typically **Added** for the test / guard, **Documentation** for **RELEASE_CHANGELOG** / **API.md** updates if integrator-facing).

Phase **2** (this spec) may add a **Documentation** bullet for the new backlog file and **RELEASE_CHANGELOG** § only, matching repository practice for spec phases.

---

## 6. Spec gate / builder checklist (phases 2b / 3)

- [x] **E1** — Default **`pytest`** fails on **`__all__`** vs **API.md** set mismatch.
- [x] **E2** — Parser scoped to the **Stable public symbols** table per normative rules.
- [x] **E3** — Actionable, contract-named failure output.
- [x] **E4** — No unnecessary new runtime dependencies.
- [x] **E5** — CI **`test`** job runs the check.
- [x] **E6** — **RELEASE_CHANGELOG.md** includes **Public export set and SemVer**.
- [x] **E7** — **CONTRIBUTING.md** points at export + changelog workflow.
- [x] **E8** — **API.md** cross-links and **Source of truth** note updated.
- [x] **CHANGELOG.md** updated for user-visible / contributor-notable delivery when implementation ships.
