# Backlog spec: Python 3.13 CI matrix readiness and policy hook

Normative **spec and acceptance criteria** for Mission Control backlog **Python 3.13 CI matrix readiness issue and policy hook** (item `a0bbc121-dec6-4f92-bd50-bfd37647dcb2`). Phase **2** (spec lead) owns this document; phase **3** (builder) implements against it; phase **2b** (spec gate) checks completeness.

**Related normative docs:** **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md#python-313-and-ci-matrix-lag-policy-hook)** (policy hook, tested vs `requires-python`); **[DEPENDENCY_LOCK_STRATEGY.md](DEPENDENCY_LOCK_STRATEGY.md#32-python-versions)** (lock + matrix); **[CONTRIBUTING.md](../CONTRIBUTING.md)**; **`.github/workflows/ci.yml`**; issue template **[`.github/ISSUE_TEMPLATE/compatibility_update.md`](../.github/ISSUE_TEMPLATE/compatibility_update.md)** (**Python interpreter / CI matrix expansion**).

---

## 1. Reconciliation with repository state

Treat the following as **facts** for builders unless a later change explicitly updates this section:

| Topic | Current state |
| ----- | ------------- |
| **`requires-python`** | **`>=3.11`** in **`pyproject.toml`** — integrator floor may be **wider** than the CI-tested set. |
| **CI `test` matrix** | **Python 3.11** and **3.12** only (**.github/workflows/ci.yml**). |
| **Lock** | Root **`uv.lock`**; jobs use **`uv sync --frozen --extra dev`** then **pytest**, **ruff**, **mypy** (no **`demo`**). |
| **Spike / readiness** | **3.13** is **not** in CI until **replayt**, **langgraph**, and **`[dev]`** tooling resolve and run cleanly on that interpreter; track blockers in the compatibility issue. |

---

## 2. Product acceptance criteria (verbatim backlog → testable IDs)

| ID | Original acceptance criterion | Normative interpretation |
| -- | ----------------------------- | ------------------------- |
| **P1** | Open or reference a **Compatibility Update** issue template checklist item for **3.13** covering **`uv.lock`** regeneration and **pytest** green. | **Before merge:** A **Compatibility Update** issue exists (new or existing) whose body uses the template’s **Python interpreter / CI matrix expansion** checklist. **Required checked evidence before closing the backlog implementation PR:** (i) **`uv.lock`** regenerated (or justified unchanged) so **`uv sync --frozen --extra dev`** succeeds on **3.13** in CI; (ii) **`uv run pytest`** with **no path/marker filter** is **green** on the **3.13** matrix leg (same contract as other Python versions). |
| **P2** | Update **`.github/workflows/ci.yml`** behind a short design note in **DESIGN_PRINCIPLES** or **DEPENDENCY_LOCK_STRATEGY** when the spike completes. | **When adding 3.13 to CI:** (i) **`.github/workflows/ci.yml`** includes **3.13** on the **`test`** job matrix (and **`supply-chain`** if that job is version-matrixed the same way); steps stay aligned with **3.11**/**3.12** (**pytest**, **ruff**, **mypy**, frozen **`[dev]`** install). (ii) **At least one** of: a one- or two-sentence note in **DESIGN_PRINCIPLES.md** (subsection **Python 3.13 and CI matrix lag**) **or** **DEPENDENCY_LOCK_STRATEGY.md** §3.2 stating that **3.13** is now part of the **tested matrix**; (iii) **DESIGN_PRINCIPLES** **Tested matrix** table row updated to list **3.13** alongside **3.11**/**3.12**. |
| **P3** | Document any skipped stdlib or upstream quirks in the issue, not only in chat. | The **Compatibility Update** issue (same as **P1**) **must** contain a **Quirks / notes** subsection (or equivalent bullets) for: **stdlib** behavior differences, **typing** or **mypy**/**ruff** edge cases, **replayt**/**langgraph**/**uv** caveats, and any **skipped** tests or **xfail** with **issue links**. Chat-only context is **not** sufficient for closure. |

---

## 3. Builder checklist (phase 3 / gate)

- [ ] **P1** — Compatibility issue filed or updated; checklist complete; lock regen + pytest green on **3.13** proven in CI logs or pasted output.
- [ ] **P2** — Workflow matrix + policy doc note + **Tested matrix** table row.
- [ ] **P3** — Quirks documented **in the issue**.
- [ ] **README** — If the **tested** Python set changes integrator-facing expectations, update compatibility lines per **DESIGN_PRINCIPLES** *Justifying new or changed runtime constraints*.
- [ ] **CHANGELOG.md** — **Unreleased** note when CI matrix or `requires-python` changes are user-visible (per **CONTRIBUTING.md**).

---

## 4. Explicit non-goals (this backlog)

- Dropping **3.11** or **3.12** from CI unless a **separate** maintainer decision says so (this spec only **adds** the path for **3.13**).
- Widening **replayt** / **langgraph** major ranges (use the rest of the **Compatibility Update** template for package majors).

---

## 5. Spec gate (phase 2b)

- [ ] **P1–P3** mapping is unambiguous and traceable from **compatibility_update.md** + this doc.
- [ ] **DESIGN_PRINCIPLES** and **DEPENDENCY_LOCK_STRATEGY** stay consistent with **README** and **MISSION** CI descriptions after implementation.
