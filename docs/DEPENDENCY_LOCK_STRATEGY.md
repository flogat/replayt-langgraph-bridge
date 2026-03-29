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
3. **Routine cadence (maintainer expectation)** — At minimum, refresh the lock when cutting releases, after security advisories, or when CI failures indicate resolver drift; optional periodic refresh (e.g. monthly) is team discretion—record the chosen habit in **CONTRIBUTING** or this doc in one sentence once decided.

## 6. Security alerts → lock updates (normative mapping)

This ties the lock to **[docs/DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md)** and existing audit CI.

| Signal | Action |
| ------ | ------ |
| **GitHub Dependabot / advisory** on a direct or transitive dependency | Regenerate the lock inside current **`pyproject.toml`** ranges if a fixed version exists; run **pytest** and **`pip-audit`** (same flags as CI). If the fix requires **widening** or changing declared ranges, follow the **Compatibility Update** template and **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md#breaking-upstream-releases--triage)**; update **CHANGELOG.md** when bounds change. |
| **`pip-audit` failure** in CI | Treat as **blocking** unless documented under **Accepted risks** in **DEPENDENCY_AUDIT.md** with matching **`--ignore-vuln`** in **`.github/workflows/ci.yml`**. Prefer **lock regen** and version bumps over ignores. |
| **Accepted transitive risk** | Document in **DEPENDENCY_AUDIT.md**; ensure the **locked** graph is what **pip-audit** scans when CI uses the lock. |

**Diff discipline:** Security or release review should use version control **diffs on the lock file** (and changelog notes for range changes) to see exactly what entered the tree.

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
