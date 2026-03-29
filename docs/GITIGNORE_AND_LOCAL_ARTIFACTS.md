# `.gitignore`, local secrets, and local artifacts (normative contributor spec)

This document is the **source of truth** for which paths the repository **should** ignore via **`.gitignore`**, which paths **must remain tracked** for reproducible builds and packaging, and how to verify changes. It implements the product intent behind tightening **`.gitignore`** for **local secrets**, **orchestration scratch**, and **local persistence dumps** without breaking **`uv`**, **setuptools**, or CI.

**Related:** **[DESIGN_PRINCIPLES.md — Secrets policy](DESIGN_PRINCIPLES.md#secrets-policy)** (behavior and redaction); **[CONTRIBUTING.md — What must never be committed](../CONTRIBUTING.md#what-must-never-be-committed)** (short checklist).

---

## 0. Backlog traceability

**Backlog:** Review and tighten **`.gitignore`** for local secrets and orchestrator artifacts (workflow item **`27853c00-77f0-403a-9ff2-6d45f3255a4f`**). Short Mission Control framing and builder checklist: **[BACKLOG_GITIGNORE_LOCAL_SECRETS.md](BACKLOG_GITIGNORE_LOCAL_SECRETS.md)**.

**User story (verbatim intent):** Contributors want **`.gitignore`** to exclude common secret filenames and local orchestration directories so accidental commits of **tokens**, **API keys**, or **private prompts** (for example content under **`.cursor/skills/`** or Mission Control handoffs under **`.orchestrator/`**) are less likely.

**Constraints from product backlog:**

- Do **not** ignore files required for reproducible builds; document intentional exceptions (**§3**, **G4**).
- **Pre-commit** hooks (detect-secrets, gitleaks, etc.) are **out of scope** for this backlog unless adopted later (**traceability table** below).

**Acceptance criteria (verbatim) → spec mapping:**

| Backlog line | Normative mapping |
| ------------ | ----------------- |
| “`.gitignore` updated with justified patterns; no overlap that breaks packaging” | **G1**, **G2**, **§4** |
| “Short note in `CONTRIBUTING.md` on what must never be committed” | **G3** — checklist at **[CONTRIBUTING.md § What must never be committed](../CONTRIBUTING.md#what-must-never-be-committed)**; bullets should stay aligned with **§2** categories **A**–**C** (and **E** where relevant). |
| “If pre-commit is added later, criteria can reference it; not required in this item.” | Paragraph under the **§5** traceability table. |

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
| **A. Environment and secrets files** | API keys and tokens often land in dotenv or ad-hoc config files. | `.env`, `.env.*`, `!.env.example` (only if the repo adds a **tracked** template named exactly `.env.example`), `.envrc`, `.direnv/`, **`.netrc`** (CLI FTP/HTTP credential store when copied into the tree), `*.pem`, `*.p12`, `*.pfx`, `id_rsa`, `id_ed25519`, `*.key` (where used for **private** key material—document if a public key filename is tracked and needs a negated rule). See **§6 Optional pattern catalog** for additional filenames to consider when contributors adopt new tooling. |
| **B. Orchestration and local agent scratch** | Mission Control and agent tools write under fixed trees; these must not enter git history. Treat skill bodies, handoffs, and private prompts as **local-only** when they live under these trees. | `.orchestrator/` (already present), **`.cursor/skills/`** (already present), **`.aider*`** (already present), alignment JSON at repo root if mis-placed (**`alignment_result.json`**, **`.alignment_result.json`**—already present). Extend only when a **new** tool writes a stable, non-portable directory name documented in this table. |
| **C. Local durable checkpoint / store dumps (dev only)** | Contributors experimenting with **SQLite**, **JSONL stores**, or LangGraph-local persistence may create files that look like production data. | Prefer **directory-scoped** ignores (e.g. `local_checkpoints/` or `scratch/`) **or** suffixes unlikely to appear in **`tests/`** fixtures (e.g. `*.dev.sqlite3`). **Do not** add a bare `*.jsonl` if the repo might commit fixture **`.jsonl`** files later—verify with `git check-ignore -v` and the full test suite. |
| **D. Python / packaging / tooling noise** | Standard hygiene; keep aligned with existing blocks. | `__pycache__/`, `*.py[cod]`, `.venv/`, `venv/`, `dist/`, `build/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `htmlcov/`, etc. (already largely present—merge duplicates when tightening). |
| **E. Placeholder / mistaken paths** | Agents sometimes create literal **`path/`** trees from examples. | Keep **`path/`** (already present) unless a future **real** top-level package needs that name (then replace with a narrower pattern and document here). |

---

## 3. Must remain tracked (intentional exceptions)

The following **must not** be ignored (treat as **forbidden ignore targets** when reviewing new globs). If a new **`.gitignore`** rule could match them, add a **`!` negation** or narrow the rule, and document the exception in a comment in **`.gitignore`** and (if non-obvious) a row below.

| Artifact / path | Why it must stay tracked |
| ----------------- | ------------------------- |
| **`pyproject.toml`** | Declares dependencies, extras, and build backend. |
| **`uv.lock`** | Frozen **`[dev]`** graph for CI and reproducible contributor installs (**[DEPENDENCY_LOCK_STRATEGY.md](DEPENDENCY_LOCK_STRATEGY.md)**). |
| **`src/replayt_langgraph_bridge/`** | Shipped package source (**`setuptools`** **`package-dir`** = **`src`**). |
| **`tests/`** | Default **pytest** **`testpaths`**; CI runs the full suite with no path filter. |
| **`docs/`** | Normative specifications and integrator-facing documentation. |
| **`.github/workflows/`** | CI definitions (e.g. **`test`**, **`supply-chain`**). |
| **`.env.example`** | Tracked, comment-only template for local environment variable **names** (no secrets). Must stay visible to Git: **`.env.*`** is ignored, so **`!.env.example`** sits **immediately** after that line in **`.gitignore`** (Category **A**). |
| **Root policy files** | **`README.md`**, **`CONTRIBUTING.md`**, **`CHANGELOG.md`**, **`SECURITY.md`**, **`LICENSE`**, **`MANIFEST.in`** (if present), and any committed **`src/**`** / **`tests/**`** data files relied on by tests. |

**Packaging verification:** After editing **`.gitignore`**, the Builder **must** run **`uv sync --frozen --extra dev`**, **`uv run pytest`** (no path or marker filter, per **CONTRIBUTING** / **REPLAYT_BOUNDARY_TESTS**), and confirm **`python -m build`** (or **`uv build`**) produces a wheel/sdist from a clean worktree **without** missing tracked files. This repository **ships** **`.env.example`**; keep **`!.env.example`** immediately under **`.env.*`** so the template is never hidden.

---

## 4. Overlap and review rules

1. **No duplicate lines** for the same intent unless one is a documented exception (e.g. root vs. subdirectory scope).
2. **Order matters** for negations: place **`!` exceptions** immediately after the pattern they override.
3. Before merging, run **`git status`** and **`git check-ignore -v <path>`** on any suspicious new local file to confirm intent.
4. If a pattern is **overly broad** (e.g. all **`*.db`**), prefer narrowing or a dedicated **`scratch/`** directory convention documented in **CONTRIBUTING**.
5. **Broad secret-like basenames** (e.g. a root-level **`credentials.json`**) are risky: they may collide with future **tracked** fixtures or sample names. Prefer **tool-specific paths** (see §6), **directory-scoped** ignores, or **`git check-ignore -v`** on a clone with representative local files before merging.

---

## 5. Product acceptance criteria (maps to backlog)

Treat the backlog **Review and tighten `.gitignore` for local secrets and orchestrator artifacts** as **done** when all of the following hold:

| ID | Criterion | How to verify |
| -- | --------- | ------------- |
| **G1** | **`.gitignore`** includes justified patterns for **secrets / env files**, **orchestration & agent scratch**, and **local checkpoint/store dumps** per §2, with comments. | File review; categories A–C satisfied without contradicting §3. |
| **G2** | **No packaging or CI regression**: reproducible **`[dev]`** install and full **pytest** still pass; sdist/wheel build still includes intended package data. | Commands in §5.1. |
| **G3** | **`CONTRIBUTING.md`** contains a short **“What must never be committed”** section (see **[CONTRIBUTING.md](../CONTRIBUTING.md#what-must-never-be-committed)**) pointing here for full rules and aligned with §2 categories (extend the bullet list if new ignore categories are added). | Doc review. |
| **G4** | Intentional **exceptions** (§3) are documented in **`.gitignore`** comments and, if subtle, in this doc (§3 table or §7). | Review. |
| **G5** | Representative **§2** paths stay enforced by **`tests/test_gitignore_contract.py`** (via **`git check-ignore`**). When you add or remove ignore rules that change expected behavior for common local filenames, extend or adjust that test in the **same** change set so CI catches spec drift. | **`uv run pytest tests/test_gitignore_contract.py`**; full suite per §5.1. |

**Pre-commit hooks:** Not required for this backlog. If the project adds **pre-commit** later, hooks such as **detect-secrets** or **gitleaks** may **supplement** but **not replace** clear **`.gitignore`** hygiene; update this section with the hook names and scope when introduced.

### 5.1 Builder verification commands (normative)

Run from a clean worktree (no unintended staged deletes). After **`.gitignore`** edits:

1. **`uv sync --frozen --extra dev`**
2. **`uv run pytest`** — no path arguments, no marker filter (same contract as CI; see **CONTRIBUTING** / **REPLAYT_BOUNDARY_TESTS**).
3. **`uv build`** or **`python -m build`** — wheel and sdist succeed; spot-check that **`src/replayt_langgraph_bridge/`** is still packaged as before.
4. **`git check-ignore -v`** on any **new** ignored path you introduced (and on **`uv.lock`**, **`pyproject.toml`**, **`src/`** sample paths) to confirm §3 **forbidden ignore targets** are **not** ignored.
5. **`uv run pytest tests/test_gitignore_contract.py`** — confirms §2 examples and §3 “must not ignore” paths still match Git’s view (**G5**).

### 5.2 When `.gitignore` already matches §2 (zero-diff audit path)

The backlog is **still satisfied** if an audit against **`master`** (or the agreed integration branch) shows **no** further patterns are justified: packaging and CI must not regress, and the social contract (CONTRIBUTING + this doc) must stay true.

**Minimum for the Builder when the `.gitignore` diff is empty:**

1. Run **§5.1** on the branch and capture pass/fail (CI parity).
2. In the PR or issue, state explicitly that **§2** categories **A**–**E** were reviewed and **no** additional globs were added **because** of collision risk (**§4**), existing coverage, or opt-in directory conventions only.
3. If local tooling exposes a **new** recurring footgun (stable relative path under the repo root), prefer **§6** + a narrow rule + **G5** in the **same** change set next time—do not treat “empty diff” as permission to skip **§5.1** on CI.

---

## 6. Optional pattern catalog (review when tightening)

Use this list when expanding **Category A** or **B**; **do not** copy it wholesale into **`.gitignore`**. Each addition needs a comment, collision check against **`tests/`** / **`docs/`** fixtures, and (if used) a row or footnote in §2.

| Pattern or path | Typical use | Risk / note |
| --------------- | ----------- | ----------- |
| **`application_default_credentials.json`** | Google ADC file often under `~/.config`; sometimes copied into a repo by mistake | Prefer ignoring a **stable relative path** if your workflow creates one locally; avoid ignoring every `**/credentials.json`. |
| **`client_secret*.json`** / **`token.json`** (OAuth desktop) | Google / OAuth client flows | High collision risk with generic names; prefer directory scope (e.g. `local_oauth/`) ignored instead. |
| **`.secrets.baseline`** | **detect-secrets** baseline (if adopted) | Often **tracked** intentionally; **never** ignore if the project commits it. |
| **`handoff.md`** under **`.orchestrator/`** | Mission Control handoffs | Covered by **`.orchestrator/`**; do not add redundant root-level `handoff.md` ignore unless a documented tool writes at repo root. |
| **`.netrc`**, **`.aws/credentials`**, **`.config/gcloud/`**-style copies | CLI / cloud credential drops next to a clone | Prefer **directory-scoped** ignores (e.g. a documented `local_secrets/` tree) over ignoring every `credentials` basename; verify **§3** with **`git check-ignore -v`**. |
| **`*.pfx`** | Windows PKCS#12-style bundles (often password-protected) | Same hygiene as **`*.p12`**; add only if contributors hit real leaks; watch for tracked fixtures with that extension. |
| **`secrets.yaml`**, **`secrets.yml`**, **`*.secrets.yaml`** | Ad-hoc app config | Very high **collision** risk with future fixtures—prefer **suffix** or **directory** conventions (e.g. `local/*.secrets.yaml`) documented in **§2** before merging a broad rule. |
| **`.vscode/settings.json`** with secrets | Editor config | Usually **tracked** for shared workspace settings; **do not** ignore wholesale—use **Secrets policy** and reviews instead. |

---

## 7. Maintainer notes

- **`.orchestrator/`** is **gitignored by design** (ephemeral Mission Control state). Do not **`git add`** it unless an explicit workflow requires it.
- **Secrets policy** for *runtime behavior* remains **[DESIGN_PRINCIPLES.md — Secrets policy](DESIGN_PRINCIPLES.md#secrets-policy)**; this document covers **version-control boundaries** only.

### 7.1 Current baseline (`.env.example` and Category **A**)

The repository **ships** a root **`.env.example`**: comment-only keys (for example optional **`OPENAI_API_KEY`**, **`ANTHROPIC_API_KEY`**, **`LANGCHAIN_*`**, **`REPLAYT_BRIDGE_STRICT_REDACT`**) with **no** values, plus short pointers to this doc and **Secrets policy**. **`.gitignore`** ignores **`.env`**, **`.env.*`**, then **`!.env.example`** on the following line so the template stays tracked (**§3**). **README** and **CONTRIBUTING** link **`.env.example`** from setup and secrets guidance; **`tests/test_gitignore_contract.py`** asserts **`git check-ignore`** does **not** match **`.env.example`** (**G5**).

**Merge-base review (normative for Builder):** From the git root, compare the feature branch to the integration branch (today **`master`**) with:

```bash
git diff master -- .gitignore CONTRIBUTING.md docs/GITIGNORE_AND_LOCAL_ARTIFACTS.md .env.example
```

If the diff is empty for **`.gitignore`**, the Builder **still** completes **G1**–**G5** by recording in the PR description (or issue) that the audit found no additional patterns needed, and by confirming **§5.1** / **`test_gitignore_contract`** pass on CI. If the diff is non-empty, cite **§2** categories in the PR.

**Changing the template:** Edits to **`.env.example`** belong in the **same** change set as any **`.gitignore`** or contract-test updates needed so **§2** / **§3** / **G5** stay true.

---

## 8. Contract tests vs this spec (drift control)

**`tests/test_gitignore_contract.py`** encodes a **small, representative** subset of §2 (env files, direnv, dev dirs, orchestration paths, placeholder **`path/`** trees) and §3 (paths that **must not** be ignored). It is **not** an exhaustive parser of **`.gitignore`**.

- When you add a **new** ignore rule for a **recurring** contributor footgun (new Category **A**–**C** glob that should hold on every clone), add a matching **`rel`** assertion in **`test_gitignore_contract.py`** in the **same** pull request (**G5**).
- When you add a **narrow, tool-specific** rule (§6), you **may** omit a new test case if this doc explains why (collision risk, opt-in directory only)—but you **must** still run **`git check-ignore -v`** as in §4–§5.1.

---

## 9. Spec gate checklist (reviewer / phase 2b)

Use this list before sending work to the **Builder** (or to approve the spec without implementation):

1. **§0** backlog traceability matches the item title, constraints, and acceptance lines the Builder will sign off against.
2. **§2** categories **A**–**E** are unambiguous; examples distinguish **must ignore** from **optional catalog** (§6).
3. **§3** lists every class of artifact that must stay tracked for **`uv.lock`** CI and packaging; no proposed glob obviously shadows **`tests/`** fixtures or **`docs/`** without a negation story.
4. **§4** overlap rules are acknowledged for any broad pattern under review.
5. **G1**–**G5** are collectively achievable; **G5** is understood as “keep contract tests honest,” not “duplicate entire **`.gitignore`** in Python.”
6. **CONTRIBUTING** “What must never be committed” mentions secrets, orchestration scratch, and local persistence experiments in line with **§2** **A**–**C** (and points here for normative detail); optional **§6**-style filenames are examples, not a second ignore list.
7. **§5.2** is understood: an empty **`.gitignore`** diff is allowed **only** with an explicit audit note and **§5.1** green.
8. **Pre-commit** remains optional per the paragraph under the traceability table.
