# Backlog spec: periodic `uv.lock` refresh (CI guardrail)

Normative **spec and acceptance criteria** for Mission Control backlog **CI guardrail: periodic uv lock refresh workflow** (item **`9c1ba44c-3880-4cb7-a1ac-4a585e2e12d6`**). Phase **2** (spec lead) owns this document; phase **3** (builder) implements against it; phase **2b** (spec gate) checks completeness.

**Goal:** Reduce **silent drift** between loose local installs (for example **`pip install -e ".[dev]"`**) and **CI’s frozen** **`[dev]`** graph, by **routinely** regenerating **`uv.lock`**, running the **same** **`pip-audit`** policy as CI, and landing updates through **reviewed** PRs (automation or a documented maintainer playbook).

**Related normative docs:** **[DEPENDENCY_LOCK_STRATEGY.md](DEPENDENCY_LOCK_STRATEGY.md)** (§5 cadence, §6 security → lock, **`pip-audit`** triage); **[DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md)** (accepted **`--ignore-vuln`** IDs); **[CONTRIBUTING.md](../CONTRIBUTING.md)** (regen commands, local audit flags); **`.github/workflows/ci.yml`** (jobs **`test`** and **`supply-chain`**); **`.github/workflows/uv-lock-refresh.yml`** (scheduled lock refresh); **[README.md](../README.md)** — **Dependency strategy**.

---

## 1. Reconciliation with repository state

Treat the following as **facts** for builders unless a later change explicitly updates this section:

| Topic | Current state |
| ----- | ------------- |
| **Lock artifact** | Root **`uv.lock`** freezes **`[dev]`** only (**no** **`demo`**). |
| **CI install** | **`uv sync --frozen --extra dev`** in jobs **`test`** and **`supply-chain`**. |
| **Lock regen (contributor)** | **`uv sync --extra dev`** (omit **`--frozen`**) per **CONTRIBUTING.md**; commit **`uv.lock`** with related **`pyproject.toml`** edits when applicable. |
| **`uv` pin in CI** | **`astral-sh/setup-uv@v5`** with **`version: "0.11.2"`** in **`.github/workflows/ci.yml`** (today). |
| **`pip-audit` invocation** | After frozen sync: **`uv run pip-audit --ignore-vuln CVE-2026-4539 --desc`** — must stay **byte-for-byte** aligned between **`.github/workflows/ci.yml`** **`supply-chain`**, **`.github/workflows/uv-lock-refresh.yml`**, **CONTRIBUTING.md**, and **DEPENDENCY_AUDIT.md** (today’s accepted-ignore set). |
| **Validation trio (test job)** | **`uv run pytest`** (no path/marker filter), **`uv run ruff check src tests`**, **`uv run mypy -p replayt_langgraph_bridge`**. |
| **Scheduled lock refresh (path A)** | **`.github/workflows/uv-lock-refresh.yml`** — weekly cron + **`workflow_dispatch`**; same **`uv`** pin as **`ci.yml`**; Python **3.12** single job for regen + checks (CI matrix still runs 3.11–3.13 on PRs). |

---

## 2. Delivery paths (choose one; preference stated)

| Path | Description | Preference |
| ---- | ----------- | ------------ |
| **A — Scheduled GitHub Actions** | A workflow under **`.github/workflows/`** runs on **`schedule`** (and should expose **`workflow_dispatch`**), regenerates the lock, runs validations, and **opens or updates a PR** when **`uv.lock`** changes. | **Preferred** |
| **B — Maintainer playbook (docs-only)** | No new scheduled workflow; instead, a **numbered runbook** in **CONTRIBUTING.md** and/or **DEPENDENCY_LOCK_STRATEGY.md** that maintainers execute on a **documented cadence**, producing a normal PR with the same checks. | **Acceptable minimum** |

The backlog is **done** when **either** path **A** **or** path **B** is fully satisfied, plus **documentation cross-links** in **§3**.

---

## 3. Product acceptance criteria (testable IDs)

| ID | Criterion | Normative interpretation |
| -- | --------- | ------------------------- |
| **L1** | **Lock regeneration** — Regenerate **`uv.lock`** for the **`[dev]`** surface without editing **`pyproject.toml`** unless a separate change requires it. | Use **`uv sync --extra dev`** (no **`--frozen`**) as in **CONTRIBUTING.md** — or an equivalent documented **`uv lock`** sequence that produces the **same** committed artifact policy (single root lock, **`[dev]`** only, **no** **`demo`**). Automation **must not** silently change declared dependency ranges. |
| **L2** | **Frozen install sanity** — After regen, prove the new lock installs. | Run **`uv sync --frozen --extra dev`**; it **must succeed** before audit/tests. |
| **L3** | **`pip-audit` policy parity** — Same tool, flags, and ignore list as CI. | Run **`uv run pip-audit`** with the **exact** arguments from **`.github/workflows/ci.yml`** job **`supply-chain`** (today **`--ignore-vuln CVE-2026-4539 --desc`**). Any new ignore **requires** the **DEPENDENCY_AUDIT.md** + workflow update path in **DEPENDENCY_LOCK_STRATEGY** §6 — the refresh workflow **must not** drift. |
| **L4** | **Test / lint / typing parity** — Same commands as job **`test`**. | From the frozen env: **`uv run pytest`**, **`uv run ruff check src tests`**, **`uv run mypy -p replayt_langgraph_bridge`** (no extra paths or markers on pytest). |
| **L5** | **Toolchain alignment** — **`uv`** (and Python) versions are predictable. | Use **`astral-sh/setup-uv@v5`** with the **same `version` string** as **`ci.yml`** unless a **single** coordinated bump updates **both** files in the same change set. Pin **`setup-python`** to **one** Python version **documented in the workflow YAML comment** or in this spec’s **§1** table after implementation (recommended default: **3.12** as a matrix midpoint; must remain consistent with **DEPENDENCY_LOCK_STRATEGY** §3.2’s single-lock story). |
| **L6** | **PR outcome (path A)** — Propose lock updates via PR when there is a diff. | If **`uv.lock`** changes, open (or update) a PR against **`master`** with a clear title (e.g. dependency / lock refresh) and body that cites **DEPENDENCY_LOCK_STRATEGY** §6 and **CONTRIBUTING** triage for **`pip-audit`** failures. If **`uv.lock`** is **unchanged**, **do not** open an empty PR; exit green. |
| **L7** | **Cadence + manual trigger (path A)** | Declare a **`schedule`** (recommended: **weekly** cron) and **`workflow_dispatch`** so maintainers can run on demand. Document the cron in a workflow comment. |
| **L8** | **Playbook (path B)** | Numbered steps: when to run (at least **weekly** or **monthly** — pick one and state it), copy-paste command block (**L1–L4** order), PR checklist (diff review, **CHANGELOG** expectations per **CONTRIBUTING** when material), and pointer to **`supply-chain`** failure triage. Location: **CONTRIBUTING.md** and/or **DEPENDENCY_LOCK_STRATEGY.md** §5. |
| **L9** | **Contributor-facing pointers** | **README.md** — **Dependency strategy** links to the **implemented** workflow file **or** the playbook section. **CONTRIBUTING.md** — **Dependency management** links the same. **DEPENDENCY_LOCK_STRATEGY.md** §5 references this backlog item as **implemented** once merged (replace “pending automation” wording). |
| **L10** | **Least privilege / scope** | Workflow does **not** install **`demo`**, does **not** require PyPI tokens, and uses default **`GITHUB_TOKEN`** only for checkout + PR creation ( **`contents: write`**, **`pull-requests: write`** as needed). No outbound vendor LLM calls. |

---

## 4. Builder checklist (phase 3 / gate)

- [x] **Path A or B** chosen; if **A**, new workflow file name and schedule documented (**`.github/workflows/uv-lock-refresh.yml`**).
- [x] **L1–L5** satisfied in automation **or** playbook runs.
- [x] **L6** (if **A**) or **L8** (if **B**) satisfied.
- [x] **L9** — **README**, **CONTRIBUTING**, **DEPENDENCY_LOCK_STRATEGY** §5 updated.
- [x] **L10** — permissions and scope verified.
- [x] If **`pip-audit`** fails after a lock refresh: follow **DEPENDENCY_LOCK_STRATEGY** triage (fix, range change + compatibility issue, or documented ignore) — the refresh automation **fails the job**; it **must not** auto-merge while red.
- [x] **CHANGELOG.md** — **Unreleased** note when the **delivered** work is user- or integrator-visible (for example new CI behavior maintainers rely on); **internal-only** playbook text with no workflow change may be omitted per **CONTRIBUTING.md** “purely internal” guidance — state the choice in the implementation PR if ambiguous.

---

## 5. Explicit non-goals (this backlog)

- Refreshing or locking the optional **`demo`** extra graph (see **DEPENDENCY_LOCK_STRATEGY** §3.3).
- Auto-merging PRs without review.
- Replacing **Dependabot** or advisory triage — this complements **§6**; it does not remove human judgment on CVEs or range bumps.
- Pinning different **`uv`** versions in the refresh workflow vs **`ci.yml`** without a coordinated bump.

---

## 6. Spec gate (phase 2b)

- [ ] **L1–L10** are unambiguous and traceable to **ci.yml**, **CONTRIBUTING.md**, and **DEPENDENCY_LOCK_STRATEGY.md**.
- [ ] **`pip-audit`** flag parity is called out so a future CI edit does not orphan the refresh workflow.
- [ ] Path **A** vs **B** is explicit in the implementation PR description.
