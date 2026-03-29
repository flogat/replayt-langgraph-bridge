# Backlog spec: Review and tighten `.gitignore` for local secrets and orchestrator artifacts

Normative **Mission Control framing** for backlog **Review and tighten `.gitignore` for local secrets and orchestrator artifacts** (item **`27853c00-77f0-403a-9ff2-6d45f3255a4f`**). Phase **2** (spec lead) owns this document; phase **3** (builder) implements against the **detailed** spec **[GITIGNORE_AND_LOCAL_ARTIFACTS.md](GITIGNORE_AND_LOCAL_ARTIFACTS.md)**; phase **2b** (spec gate) checks that mapping stays unambiguous.

**Single source of truth** for patterns, exceptions, overlap rules, and the **G1**–**G5** acceptance table: **[GITIGNORE_AND_LOCAL_ARTIFACTS.md](GITIGNORE_AND_LOCAL_ARTIFACTS.md)** (§0–§9).

**Related:** **[DESIGN_PRINCIPLES.md — Secrets policy](DESIGN_PRINCIPLES.md#secrets-policy)**; **[CONTRIBUTING.md — What must never be committed](../CONTRIBUTING.md#what-must-never-be-committed)**; **README.md** (secrets + `.gitignore` pointers); **`tests/test_gitignore_contract.py`** (**G5**).

---

## 1. Reconciliation with repository state

Treat the following as the **baseline** unless a later commit explicitly changes it:

| Topic | Snapshot |
| ----- | -------- |
| **Root `.gitignore`** | Categories **A**–**E** populated per **[GITIGNORE_AND_LOCAL_ARTIFACTS.md](GITIGNORE_AND_LOCAL_ARTIFACTS.md)** §2 (env/secrets, orchestration and agent scratch including **`.orchestrator/`** and **`.cursor/skills/`**, local checkpoint dirs / dev SQLite suffix, Python and tooling noise, placeholder **`path/`**). |
| **`CONTRIBUTING.md`** | **What must never be committed** exists and links **`GITIGNORE_AND_LOCAL_ARTIFACTS.md`** and **`test_gitignore_contract.py`**. |
| **Contract tests** | **`tests/test_gitignore_contract.py`** asserts representative ignored vs not-ignored paths via **`git check-ignore`**. |

**Builder implication:** The implementation PR may show an **empty** **`.gitignore`** diff if **`master`** already satisfies §2; in that case **[GITIGNORE_AND_LOCAL_ARTIFACTS.md](GITIGNORE_AND_LOCAL_ARTIFACTS.md)** §5.2 still applies (explicit audit note + §5.1 verification green).

---

## 2. Product intent (backlog wording → spec)

| Source | Text |
| ------ | ---- |
| **User story** | As a contributor, I want **`.gitignore`** to exclude common secret filenames and local orchestration directories so accidental commits of tokens or private prompts are less likely. |
| **Context** | Expand coverage for **`.env`**, key files, and local checkpoint dumps as the project grows—without breaking packaging. |
| **Constraints** | Do not ignore files required for reproducible builds; document intentional exceptions. |

**Normative reading:** **Private prompts** and non-portable agent content belong under **Category B** (orchestration / local agent scratch), typically **`.orchestrator/`** or **`.cursor/skills/`**. **Category A** covers environment files and common private-key material. **Category C** covers dev checkpoint dumps; prefer directory-scoped ignores or **`*.dev.sqlite3`** over unreviewed **`*.db`** / **`*.jsonl`** globs (**GITIGNORE** §4, §6).

---

## 3. Acceptance mapping (verbatim backlog ↔ **G1**–**G5**)

| Original acceptance criterion | Where defined | How to close |
| ----------------------------- | ------------- | ------------ |
| “`.gitignore` updated with justified patterns; no overlap that breaks packaging” | **G1**, **G2**; §2, §4 | File review + §5.1 commands in **GITIGNORE** |
| “Short note in `CONTRIBUTING.md` on what must never be committed” | **G3** | Section present; extend bullets only if §2 gains a **new** category |
| “Do not ignore files required for reproducible builds; document intentional exceptions” | **G4**; §3 | **`!.env.example`** placement, no ignore on **`uv.lock`** / **`pyproject.toml`** / **`src/`** / **`tests/`** / **`.github/workflows/`** |
| Contract / CI enforcement | **G5**; §8 | **`test_gitignore_contract.py`** updated in the **same** PR when recurring ignore behavior changes |
| Pre-commit hooks | **GITIGNORE** §5 | **Out of scope** unless adopted later |

---

## 4. Builder checklist (phase 3 / gate)

- [ ] **Diff review** — `git diff master -- .gitignore CONTRIBUTING.md docs/GITIGNORE_AND_LOCAL_ARTIFACTS.md docs/BACKLOG_GITIGNORE_LOCAL_SECRETS.md .env.example` (or agreed integration branch).
- [ ] **G1**–**G4** — Per **[GITIGNORE_AND_LOCAL_ARTIFACTS.md](GITIGNORE_AND_LOCAL_ARTIFACTS.md)** §2–§5.1; if **`.gitignore`** unchanged, §5.2 audit note in PR.
- [ ] **G5** — Contract tests match new or removed **recurring** ignore rules (**GITIGNORE** §8).
- [ ] **CHANGELOG.md** — **Unreleased** bullet when contributor-visible **`.gitignore`** or policy text changes (**CONTRIBUTING.md**); optional for **spec-only** doc adds if maintainers treat them as internal (otherwise document under **Documentation**).

---

## 5. Non-goals

- Mandatory **pre-commit** secret scanning tools.
- Wholesale ignores of shared editor trees (e.g. all of **`.vscode/`**) when the repo tracks workspace settings (**GITIGNORE** §6).
- Broad **`*.jsonl`** / **`*.db`** patterns without §4 collision analysis.

---

## 6. Spec gate (phase 2b)

- [ ] Mission Control item **`27853c00-77f0-403a-9ff2-6d45f3255a4f`** is traceable from this doc and **GITIGNORE_AND_LOCAL_ARTIFACTS** §0.
- [ ] **G5** is understood as representative **`git check-ignore`** coverage, not a duplicate parser of **`.gitignore`**.
- [ ] **§5.2** zero-diff path is explicit for branches that only document or verify existing rules.
