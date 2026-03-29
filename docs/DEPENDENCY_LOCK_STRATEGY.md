# Dependency lock strategy (reproducible CI and release branches)

This document is the **normative specification** for backlog **Add reproducible lock or constraint strategy for release branches**. It defines what the **Builder** must implement so dependency resolution for automated checks is **repeatable**, **diffable**, and aligned with **[docs/DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md#dependency-and-pin-policy)** and **[README.md](../README.md)**.

**Status:** Root **`uv.lock`** freezes the **`[dev]`** install (core + **pytest** / **ruff** / **pip-audit** / **mypy**, **no** **`demo`**). CI jobs **`test`** and **`supply-chain`** use **`uv sync --frozen --extra dev`**; regeneration commands live in **CONTRIBUTING.md**.

## 1. Goals

1. **Reproducible resolution** — The same commit (especially on **release branches** and tags) must yield the **same resolved dependency graph** for the install surface CI uses to run tests and supply-chain checks, modulo intentional lock updates.
2. **Diffable graphs** — Security response and incident review can **diff** lock revisions to see **exact** version changes across direct and transitive dependencies (bridge stack is sensitive to upstream patch behavior).
3. **Policy alignment** — Locked surface must match the **core + `dev`** contract: **`[dev]`** only for the primary CI path—**no** optional **`demo`** extra in that lock unless the team explicitly chooses a **second** artifact for optional verification (see §3.3).

## 2. Allowed primary artifacts (pick one; document the choice in the PR)

The Builder **must** commit **one** of the following (team-approved; default recommendation below).

| Approach | Committed artifact(s) | Typical regeneration |
| -------- | --------------------- | -------------------- |
| **A. uv (recommended)** | `uv.lock` at repository root | `uv lock` (after `pyproject.toml` dependency edits); install with `uv sync --frozen` (and flags for extras / Python as documented in CONTRIBUTING) |
| **B. pip-tools** | e.g. `requirements-ci.txt` (+ optional `requirements-ci.in`) with **PEP 503 hashes** | `pip-compile --generate-hashes`; install with `pip install -r requirements-ci.txt` |
| **C. Other** | Maintainer-proposed, documented here and in **CONTRIBUTING** | Must meet the same **builder checklist** (§6) |

**Recommendation:** **uv** — single `uv.lock`, fast lock/regen, clear `--frozen` semantics, good fit for `pyproject.toml` + optional extras.

## 3. Scope of what must be locked

### 3.1 Minimum locked install surface

The lock **must** cover exactly what the **`test`** job needs today: **editable install of the package with the `dev` extra** (core runtime deps + **pytest**, **ruff**, **pip-audit**, **mypy**), equivalent to:

```bash
pip install -e ".[dev]"
```

After implementation, **at least one** CI job (see §4) **must** install using **only** the committed lock/constraints artifact (plus the local project), not an unconstrained `pip install -e ".[dev]"` that re-resolves from PyPI on every run.

### 3.2 Python versions

CI runs **Python 3.11**, **3.12**, and **3.13** (`.github/workflows/ci.yml` **`test`** and **`supply-chain`** matrices). The Builder **must** either:

- Maintain **one** lock strategy that supports **every** matrix interpreter (uv’s unified **`uv.lock`** with per-version **`uv sync --frozen`**), **or**
- Commit **separate** lock artifacts per Python minor **only if** documented with explicit regen commands for each.

Either way, **each matrix job** must install from the documented artifact(s) so resolution is frozen for that job.

**Python 3.13:** The **`test`** and **`supply-chain`** jobs include **3.13**; root **`uv.lock`** remains the single frozen graph for **`[dev]`** on all three minors. Rollout notes: **[docs/COMPATIBILITY_UPDATE_PYTHON_313.md](COMPATIBILITY_UPDATE_PYTHON_313.md)**. The next Python minor should repeat the **Compatibility Update** checklist and **[BACKLOG_PYTHON_313_CI_MATRIX.md](BACKLOG_PYTHON_313_CI_MATRIX.md)** pattern.

### 3.3 Optional `demo` extra

**Default:** Do **not** include **`demo`** in the primary CI lock. That preserves the current contract: default CI proves the integrator-relevant path without vendor LLM client packages.

If maintainers later want a **second** locked file for **`[demo]`** verification, treat it as a **follow-up**: document regen, keep **`test`** on **`[dev]`** only, and reference **[DESIGN_PRINCIPLES.md — Core vs demo extras](DESIGN_PRINCIPLES.md#core-vs-demo-extras-llm-clients-and-supply-chain)**.

## 4. CI requirements

1. **At least one job** in `.github/workflows/ci.yml` **must** install dependencies **from the committed lock or hashed constraints file** (frozen / hash-verified install), then run the same steps as today (e.g. **pytest** and **ruff** for **`test`**).
2. **Recommended:** Align **`supply-chain`** with the **same** locked install before **`pip-audit`**, so the audited graph matches the test graph. If only one job is migrated in the first PR, the handoff should say so; the backlog is minimally satisfied with **one** job.
3. **Contributor parity:** **CONTRIBUTING.md** **must** document how to create the same environment locally (e.g. `uv sync` or `pip install -r …`).

## 5. Regeneration and review cadence

1. **When to regenerate** — Any PR that changes **`[project.dependencies]`**, **`[project.optional-dependencies]`**, or **`requires-python`** in a way that affects the locked surface **must** include an updated lock/constraints file in the same change set (or a clearly linked commit).
2. **How to document** — **CONTRIBUTING.md** **must** list the exact commands (copy-paste ready) for regenerating the artifact(s), including any required tool install (e.g. `uv` version pin or `pip install pip-tools`).
3. **Routine cadence (maintainer expectation)** — At minimum, refresh the lock when cutting releases, after security advisories, or when CI failures indicate resolver drift. **Scheduled lock refresh** is **implemented** in **`.github/workflows/uv-lock-refresh.yml`** (weekly cron plus **`workflow_dispatch`**): regenerates **`uv.lock`** for **`[dev]`**, runs the same **`pip-audit`** flags as job **`supply-chain`**, then **pytest** / **ruff** / **mypy** matching job **`test`**, and opens or updates a PR when **`uv.lock`** changes. Normative detail and acceptance IDs **L1–L10**: **[BACKLOG_UV_LOCK_REFRESH_WORKFLOW.md](BACKLOG_UV_LOCK_REFRESH_WORKFLOW.md)** (Mission Control **`9c1ba44c-3880-4cb7-a1ac-4a585e2e12d6`**).

## 6. Security alerts → lock updates (normative mapping)

This ties the lock to **[docs/DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md)** and existing audit CI.

| Signal | Action |
| ------ | ------ |
| **GitHub Dependabot / advisory** on a direct or transitive dependency | Regenerate the lock inside current **`pyproject.toml`** ranges if a fixed version exists; run **pytest** and **`pip-audit`** (same flags as CI). If the fix requires **widening** or changing declared ranges, follow the **Compatibility Update** template and **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md#breaking-upstream-releases--triage)**; update **CHANGELOG.md** when bounds change. |
| **`pip-audit` failure** in CI | Treat as **blocking** unless documented under **Accepted risks** in **DEPENDENCY_AUDIT.md** with matching **`--ignore-vuln`** in **`.github/workflows/ci.yml`** and **`.github/workflows/uv-lock-refresh.yml`** (same flags). Prefer **lock regen** and version bumps over ignores. |
| **Accepted transitive risk** | Document in **DEPENDENCY_AUDIT.md**; ensure the **locked** graph is what **pip-audit** scans when CI uses the lock. |

**Diff discipline:** Security or release review should use version control **diffs on the lock file** (and changelog notes for range changes) to see exactly what entered the tree.

### pip-audit / `supply-chain` job failure triage (maintainer playbook)

This subsection is the **SLA-style playbook** for failures in GitHub Actions job **`supply-chain`** (after **`uv sync --frozen --extra dev`**, step **`Run supply-chain audit`**: **`uv run pip-audit`** with the same flags as **[docs/DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md)**). It complements the table above and **[CONTRIBUTING.md](../CONTRIBUTING.md)** so lock refreshes stay **boring** and **traceable**. User-visible security fixes follow **[docs/SECURITY_REPORTING_SPEC.md](SECURITY_REPORTING_SPEC.md)**.

#### Severity and what CI enforces

- **`pip-audit`** reports **CVE-style identifiers** (and with **`--desc`**, short descriptions). The PyPA CLI used in CI **does not** expose a “only high/critical” gate: **any** finding fails **`supply-chain`** (and the **UV lock refresh** workflow) unless that CVE is listed in **`--ignore-vuln`** and documented under **Accepted risks** in **DEPENDENCY_AUDIT.md** (mirrored in **`.github/workflows/ci.yml`** job **`supply-chain`** and **`.github/workflows/uv-lock-refresh.yml`**).
- **CVSS / vendor severity labels** (if present in advisory text) inform **how fast** maintainers act and how prominently **CHANGELOG.md** calls the work out; they **do not** override the binary pass/fail unless the project adds a different tool or policy later (today: **fail on any reported CVE** except documented ignores).

#### Response expectations (maintainer-facing)

| Situation | Target handling |
| --------- | ---------------- |
| **New CVE on a direct or transitive dep** with a **patched version** resolvable inside current **`pyproject.toml`** ranges | Land a **lock refresh** (**`uv sync --extra dev`**, commit **`uv.lock`**) and green **pytest** / **`pip-audit`** locally in the **same PR**; merge on the **normal integration cadence** (do not leave **`master`** red overnight without an owner). |
| **Fix requires range / extra / `requires-python` change** | Open or extend a **Compatibility Update** issue (**[`.github/ISSUE_TEMPLATE/compatibility_update.md`](../.github/ISSUE_TEMPLATE/compatibility_update.md)**), follow **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md#breaking-upstream-releases--triage)**; ship constraint + lock + docs + **CHANGELOG** in one coherent change set when possible. |
| **No fixed release yet** or fix is **infeasible** in-tree | Document **Accepted risk** in **DEPENDENCY_AUDIT.md** (exploitability in **this** repo’s usage, upstream tracking link or issue reference, removal criteria), add the matching **`--ignore-vuln`** flag(s) to **`.github/workflows/ci.yml`** job **`supply-chain`** and **`.github/workflows/uv-lock-refresh.yml`** so local and CI invocations stay identical. **Escalation:** coordinated disclosure or embargoed issues follow **[SECURITY_REPORTING_SPEC.md](SECURITY_REPORTING_SPEC.md)** and root **`SECURITY.md`**—do not discuss non-public details in open PRs. |
| **False positive / scanner mismatch** | Prefer an **upstream issue** (PyPI metadata, advisory DB, or dependency maintainer) linked from **DEPENDENCY_AUDIT.md**; only then a documented ignore with the same **workflow parity** as other accepted risks. |

#### Prefer refreshing `uv.lock` (default path)

1. Reproduce with **`uv sync --frozen --extra dev`** then **`uv run pip-audit`** using the **exact flags** from **CONTRIBUTING.md**, **`.github/workflows/ci.yml`** job **`supply-chain`**, and **`.github/workflows/uv-lock-refresh.yml`**.
2. Identify the **vulnerable distribution(s)** in the output; use **`uv lock`** / **`uv sync --extra dev`** (without **`--frozen`**) to pull **patched** versions **within** declared ranges.
3. Run **`uv run pytest`**, **`uv run ruff check src tests`**, and **`uv run mypy -p replayt_langgraph_bridge`** as in job **`test`**; re-run **`pip-audit`** until clean or until you move to the documented-ignore path.
4. Commit **`uv.lock`** (and **`pyproject.toml`** only if ranges or extras changed). PR description should name **CVE IDs** and **packages** bumped.

#### When *not* to rely on a lock-only bump

Use the **documented ignore** path (plus upstream tracking) when:

- There is **no** non-vulnerable version **compatible** with current **`pyproject.toml`** bounds, and widening bounds is **deferred** (must still be tracked on a **Compatibility Update** or security issue with a dated review note).
- The advisory is **confirmed** not applicable to how the dependency is **used** in this repository (document the reasoning in **DEPENDENCY_AUDIT.md** so the next maintainer can re-evaluate).

**Never** add **`--ignore-vuln`** in CI without a matching **Accepted risks** entry and a **removal criterion** (e.g. “drop ignore when **`uv.lock`** resolves to **`pygments` ≥ x.y.z**”).

#### Changelog and audit trail

- **Lock-only** refresh that **only** picks up patched transitive versions: add an **`[Unreleased]`** bullet under **`### Security`** or **`### Fixed`** (or a clearly labeled **Security** sub-bullet under **`### Changed`**) per **[SECURITY_REPORTING_SPEC.md](SECURITY_REPORTING_SPEC.md#3-changelog-and-release-process)** and **[CONTRIBUTING.md](../CONTRIBUTING.md)** when the CVE is **material** to integrators or dev installs; trivial dev-tool-only advisories may still warrant a short **Documentation** or **Security** note so release notes stay honest.
- **`pyproject.toml`** range or extra changes: follow **[RELEASE_CHANGELOG.md](RELEASE_CHANGELOG.md)** — include **before → after** bounds and point readers at **DEPENDENCY_AUDIT.md** for accepted residual risk.
- Update **DEPENDENCY_AUDIT.md** **Current Status** / **History** when ignores or major audit outcomes change so **DEPENDENCY_LOCK_STRATEGY** §6 and CI stay in sync.

## 7. Relationship to integrators

Published **PyPI** installs remain governed by **`pyproject.toml`** ranges; integrators do **not** receive the bridge’s CI lockfile as their install contract. The lock exists so **this repository’s** CI and **release-branch** checkouts are reproducible and auditable.

## 8. Builder-facing acceptance checklist (backlog completion)

Treat backlog **Add reproducible lock or constraint strategy for release branches** as **done** when **all** are true:

- [x] A **committed** lock or **hashed** constraints file (or documented set of files) lives in the repo and matches §3–§4.
- [x] **CONTRIBUTING.md** explains **when** and **how** to regenerate the artifact(s) (commands verbatim).
- [x] **At least one** CI job installs from that artifact with **frozen / hash-verified** semantics.
- [x] **README** **Dependency strategy** (or a single sentence there) points to this doc and states that CI uses the lock/constraints (once merged).
- [x] **DESIGN_PRINCIPLES.md** table or subsection for “what CI exercises” references the lock and stays consistent with **README**.
- [x] **DEPENDENCY_AUDIT.md** states that supply-chain audit runs against the **same resolved graph** as the locked CI install when applicable.
- [x] §6 **Security alerts → lock updates** is satisfied in process docs (this file + **CONTRIBUTING** / **DEPENDENCY_AUDIT** cross-links as implemented by the Builder).

Optional follow-up (not required for this backlog): second lock for **`[demo]`**, or pinning **`uv`** / **`pip-tools`** in CI for extra hermeticity.
