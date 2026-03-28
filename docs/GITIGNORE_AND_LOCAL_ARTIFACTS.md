# `.gitignore`, local secrets, and local artifacts (normative contributor spec)

This document is the **source of truth** for which paths the repository **should** ignore via **`.gitignore`**, which paths **must remain tracked** for reproducible builds and packaging, and how to verify changes. It implements the product intent behind tightening **`.gitignore`** for **local secrets**, **orchestration scratch**, and **local persistence dumps** without breaking **`uv`**, **setuptools**, or CI.

**Related:** **[DESIGN_PRINCIPLES.md — Secrets policy](DESIGN_PRINCIPLES.md#secrets-policy)** (behavior and redaction); **[CONTRIBUTING.md — What must never be committed](../CONTRIBUTING.md#what-must-never-be-committed)** (short checklist).

---

## 1. Goals

1. Reduce accidental commits of **credentials**, **environment files**, and **private agent/orchestration** output.
2. Keep **reproducible installs** intact: committed **`uv.lock`**, **`pyproject.toml`**, **`src/`**, **`tests/`**, **`.github/workflows/`**, and other files required for **`uv sync --frozen --extra dev`** and **`python -m build`** (or equivalent) **must not** be ignored.
3. Prefer **commented, grouped** patterns in **`.gitignore`** so each block states *why* it exists.

---

## 2. Required pattern categories (builder checklist)

The Builder **must** ensure **`.gitignore`** covers at least the following **categories**. Exact glob lines may evolve; every addition needs a **one-line comment** (or section header) tying it to a category below.

| Category | Rationale | Examples of patterns to include (illustrative; adjust for collisions) |
| -------- | --------- | ------------------------------------------------------------------------ |
| **A. Environment and secrets files** | API keys and tokens often land in dotenv or ad-hoc config files. | `.env`, `.env.*`, `!.env.example` (only if the repo adds a **tracked** template named exactly `.env.example`), `.envrc`, `.direnv/`, `*.pem`, `*.p12`, `id_rsa`, `id_ed25519`, `*.key` (where used for **private** key material—document if a public key filename is tracked and needs a negated rule). |
| **B. Orchestration and local agent scratch** | Mission Control and agent tools write under fixed trees; these must not enter git history. | `.orchestrator/` (already present), **`.cursor/skills/`** (already present), **`.aider*`** (already present), alignment JSON at repo root if mis-placed (**`alignment_result.json`**, **`.alignment_result.json`**—already present). Extend only when a **new** tool writes a stable, non-portable directory name documented in this table. |
| **C. Local durable checkpoint / store dumps (dev only)** | Contributors experimenting with **SQLite**, **JSONL stores**, or LangGraph-local persistence may create files that look like production data. | Prefer **directory-scoped** ignores (e.g. `local_checkpoints/` or `scratch/`) **or** suffixes unlikely to appear in **`tests/`** fixtures (e.g. `*.dev.sqlite3`). **Do not** add a bare `*.jsonl` if the repo might commit fixture **`.jsonl`** files later—verify with `git check-ignore -v` and the full test suite. |
| **D. Python / packaging / tooling noise** | Standard hygiene; keep aligned with existing blocks. | `__pycache__/`, `*.py[cod]`, `.venv/`, `venv/`, `dist/`, `build/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `htmlcov/`, etc. (already largely present—merge duplicates when tightening). |
| **E. Placeholder / mistaken paths** | Agents sometimes create literal **`path/`** trees from examples. | Keep **`path/`** (already present) unless a future **real** top-level package needs that name (then replace with a narrower pattern and document here). |

---

## 3. Must remain tracked (intentional exceptions)

The following **must not** be ignored. If a new **`.gitignore`** rule could match them, add a **`!` negation** or narrow the rule, and document the exception in a comment in **`.gitignore`** and (if non-obvious) a row below.

| Artifact / path | Why it must stay tracked |
| ----------------- | ------------------------- |
| **`pyproject.toml`** | Declares dependencies, extras, and build backend. |
| **`uv.lock`** | Frozen **`[dev]`** graph for CI and reproducible contributor installs (**[DEPENDENCY_LOCK_STRATEGY.md](DEPENDENCY_LOCK_STRATEGY.md)**). |
| **`src/replayt_langgraph_bridge/`** | Shipped package source (**`setuptools`** **`package-dir`** = **`src`**). |
| **`tests/`** | Default **pytest** **`testpaths`**; CI runs the full suite with no path filter. |
| **`docs/`** | Normative specifications and integrator-facing documentation. |
| **`.github/workflows/`** | CI definitions (e.g. **`test`**, **`supply-chain`**). |
| **Root policy files** | **`README.md`**, **`CONTRIBUTING.md`**, **`CHANGELOG.md`**, **`SECURITY.md`**, **`LICENSE`**, **`MANIFEST.in`** (if present), and any committed **`src/**`** / **`tests/**`** data files relied on by tests. |

**Packaging verification:** After editing **`.gitignore`**, the Builder **must** run **`uv sync --frozen --extra dev`**, **`uv run pytest`** (no path or marker filter, per **CONTRIBUTING** / **REPLAYT_BOUNDARY_TESTS**), and confirm **`python -m build`** (or **`uv build`**) produces a wheel/sdist from a clean worktree **without** missing tracked files. If the project adds a **tracked** **`.env.example`**, ensure ignore rules for **`.env*`** do not exclude it (**`!.env.example`**).

---

## 4. Overlap and review rules

1. **No duplicate lines** for the same intent unless one is a documented exception (e.g. root vs. subdirectory scope).
2. **Order matters** for negations: place **`!` exceptions** immediately after the pattern they override.
3. Before merging, run **`git status`** and **`git check-ignore -v <path>`** on any suspicious new local file to confirm intent.
4. If a pattern is **overly broad** (e.g. all **`*.db`**), prefer narrowing or a dedicated **`scratch/`** directory convention documented in **CONTRIBUTING**.

---

## 5. Product acceptance criteria (maps to backlog)

Treat the backlog **Review and tighten `.gitignore` for local secrets and orchestrator artifacts** as **done** when all of the following hold:

| ID | Criterion | How to verify |
| -- | --------- | ------------- |
| **G1** | **`.gitignore`** includes justified patterns for **secrets / env files**, **orchestration & agent scratch**, and **local checkpoint/store dumps** per §2, with comments. | File review; categories A–C satisfied without contradicting §3. |
| **G2** | **No packaging or CI regression**: reproducible **`[dev]`** install and full **pytest** still pass; sdist/wheel build still includes intended package data. | Commands in §3. |
| **G3** | **`CONTRIBUTING.md`** contains a short **“What must never be committed”** section (see **[CONTRIBUTING.md](../CONTRIBUTING.md#what-must-never-be-committed)**) pointing here for full rules. | Doc review. |
| **G4** | Intentional **exceptions** (§3) are documented in **`.gitignore`** comments and, if subtle, in this doc. | Review. |

**Pre-commit hooks:** Not required for this backlog. If the project adds **pre-commit** later, hooks such as **detect-secrets** or **gitleaks** may **supplement** but **not replace** clear **`.gitignore`** hygiene; update this section with the hook names and scope when introduced.

---

## 6. Maintainer notes

- **`.orchestrator/`** is **gitignored by design** (ephemeral Mission Control state). Do not **`git add`** it unless an explicit workflow requires it.
- **Secrets policy** for *runtime behavior* remains **[DESIGN_PRINCIPLES.md — Secrets policy](DESIGN_PRINCIPLES.md#secrets-policy)**; this document covers **version-control boundaries** only.
