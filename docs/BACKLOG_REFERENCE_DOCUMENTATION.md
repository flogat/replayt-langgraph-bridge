# Backlog spec: `docs/reference-documentation/` — optional upstream LangGraph / replayt mirrors

Normative **spec and acceptance criteria** for Mission Control backlog **`docs/reference-documentation: optional upstream LangGraph/replayt mirrors`** (item **`0867a72f-8b61-4a00-b076-ddb45cd1b7c8`**). Phase **2** (spec lead) owns this document; phase **3** (builder) implements against it; phase **2b** (spec gate) checks completeness.

**Scope:** **Documentation only** — no production Python changes, no new runtime dependencies, no CI jobs that require network fetches to pass.

**Related normative docs:** **`pyproject.toml`** (`[project.dependencies]` and comments); **`uv.lock`** (exact resolved versions for the frozen **`[dev]`** graph); **[DESIGN_PRINCIPLES.md — Dependency and Pin Policy](DESIGN_PRINCIPLES.md#dependency-and-pin-policy)**; **[README.md](../README.md#reference-documentation-optional)**; **[HOSTED_DEPLOYMENT_AUTHZ.md](HOSTED_DEPLOYMENT_AUTHZ.md)** (existing upstream pointers for hosted deployment).

---

## 1. Reconciliation with repository state

Treat the following as **facts** for builders unless a later change explicitly updates this section:

| Topic | Current state |
| ----- | ------------- |
| **Declared runtime bounds** | **`replayt`**: `>=0.4.0,<0.5`; **`langgraph`**: `>=1.1.0,<1.2`** — see **`pyproject.toml`**. |
| **Resolved pins for CI / lock users** | Root **`uv.lock`** freezes the transitive graph for **`uv sync --frozen --extra dev`**; exact **patch** versions drift as the lock is regenerated. |
| **README** | **[README.md](../README.md#reference-documentation-optional)** points at **`docs/reference-documentation/README.md`**, **`links.manifest.json`**, **`bridge-integration-notes.md`**, and this backlog spec (**R8** / **R9** satisfied for the shipped tree). |
| **Integrator-facing pin story** | **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md#current-dependency-constraints)** — **Current dependency constraints**; keep wording consistent when describing how mirrors relate to pins. |

---

## 2. Problem statement (verbatim intent → normative)

| Source | Normative intent |
| ------ | ---------------- |
| Backlog body | Provide **optional**, **version-aware** upstream documentation **mirrors** under **`docs/reference-documentation/`** so contributors, agents, and integrators can review **replayt** and **LangGraph** context **offline** or without hunting the live web, **without** changing runtime code. |
| Licensing | Use **short, attributed excerpts** and/or a **links manifest** only where **upstream license and terms** allow redistribution or deep linking; do **not** commit full upstream doc trees if license or vendor policy forbids it. |

---

## 3. Product acceptance criteria (testable IDs)

| ID | Acceptance criterion | Normative interpretation |
| -- | -------------------- | ------------------------- |
| **R1** | **`docs/reference-documentation/`** exists in the **tracked** tree with a **`README.md`** at that directory root. | Directory and **`README.md`** are committed under **`docs/reference-documentation/`** (not elsewhere). |
| **R2** | **`README.md` explains pin alignment** with **`pyproject.toml`**. | Must state explicitly: (i) the **declared** compatibility ranges for **`replayt`** and **`langgraph`** come from **`[project.dependencies]`**; (ii) **exact** versions used in maintainer/CI workflows come from **`uv.lock`** when using **`uv sync --frozen`**, and may differ from “latest in range” at any moment. |
| **R3** | **`README.md` describes refresh cadence.** | Must name **when** mirrors are updated (minimum: **on any bump** to **`replayt`** or **`langgraph`** bounds in **`pyproject.toml`**, and **whenever `uv.lock` is regenerated for a compatibility-related change**). May add optional **calendar** cadence (e.g. quarterly review) as a **supplement**, not a substitute for bump-driven refresh. |
| **R4** | **Licensing and provenance** are documented for every **copied excerpt**. | For each **markdown (or text) file** that contains **copied** upstream prose or large quotes: a **header block** (or equivalent front matter) with **source URL**, **upstream version or commit/tag** (or **retrieval date** if the source is not version-tagged), **license name or SPDX identifier** (or a statement that the excerpt is **fair use / short quotation** per project legal guidance), and a line that **upstream docs remain authoritative**. If the team chooses **links-only** for a given upstream page because copying is not allowed, that page appears only in the manifest (**R5**) — no bare copy without provenance. |
| **R5** | **Coverage of both upstreams** — excerpts and/or manifest. | Deliver **at least one** of: **(a)** curated **markdown excerpts**, **(b)** a **manifest** (YAML or JSON is fine) listing **canonical upstream URLs** with **version or date** metadata, **(c)** both. The combined deliverable must **explicitly cover replayt and LangGraph** topics relevant to **this bridge** (minimum: **replayt** — `Workflow` / `Runner` / execution or checkpoint concepts the bridge depends on; **LangGraph** — graph compilation, **state**, **checkpoints** / checkpointers at the level the bridge integrates). **Demo-only** stacks (**`[demo]`** extra) are **out of scope** unless a sentence in **`README.md`** says optional future expansion. |
| **R6** | **Manifest fields** (if **R5(b)** or **(c)** is used). | Each manifest entry must include: **`url`**, **`title` or `topic`**, **`pin_note`** (how it relates to **`pyproject.toml`** ranges or **`uv.lock`** line), and **`last_reviewed`** (ISO date or **`CHANGELOG` / PR** reference). |
| **R7** | **No runtime or test harness changes** required to “use” the folder. | Adding this documentation **must not** add imports, packaging **`package-data`** requirements, or **pytest** expectations that read these files unless a **separate** backlog explicitly asks for doc drift tests. |
| **R8** | **Discoverability from the root README.** | **[README.md](../README.md#reference-documentation-optional)** must point to **`docs/reference-documentation/README.md`** and to **this backlog spec** until the implementation is merged and the gate passes (after that, README may keep a short pointer to the folder README only, if desired). |
| **R9** | **README accuracy after implementation.** | Replace or amend the sentence that says the checkout **does not yet include** the folder so it matches reality (**present** and described). |

---

## 4. Builder checklist (phase 3 / gate)

- [x] **R1** — **`docs/reference-documentation/README.md`** exists.
- [x] **R2** — Pin alignment with **`pyproject.toml`** and **`uv.lock`** explained.
- [x] **R3** — Refresh cadence documented.
- [x] **R4** — Provenance / licensing for excerpts; links-only where copying is disallowed.
- [x] **R5** — Both **replayt** and **LangGraph** represented (excerpts and/or manifest).
- [x] **R6** — Manifest schema satisfied if a manifest is shipped.
- [x] **R7** — No accidental coupling to runtime or tests.
- [x] **R8** — Root **README** links updated.
- [x] **R9** — Root **README** no longer claims the folder is missing.
- [x] **CHANGELOG.md** — Under **Unreleased**, add a short **Documentation** bullet when the folder and mirrors land (integrators and offline readers benefit); omit only if **CONTRIBUTING.md** explicitly exempts pure internal backlog docs (it does not — treat as user-visible doc addition).

---

## 5. Explicit non-goals

- **Full-site mirrors** or automated scraping of upstream documentation in CI.
- **Replacing** upstream docs as the authoritative specification for **replayt** or **LangGraph**.
- **Mirroring vendor LLM provider docs** (OpenAI, Anthropic, etc.) — optional samples already point upstream; keep this backlog focused on **replayt** + **`langgraph`** integration context.
- **Legal review** beyond maintainer judgment and upstream license badges: if uncertain, prefer **R5(b)** links manifest over long excerpts.

---

## 6. Spec gate (phase 2b)

- [x] **R1–R9** are traceable from this doc and verifiable in a PR diff (file tree + README).
- [x] Wording stays consistent with **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md#dependency-and-pin-policy)** and **[README.md](../README.md)** compatibility lines.
- [x] No **`.orchestrator/`** or other gitignored scratch is used as the **only** location for shipped mirrors — committed path is **`docs/reference-documentation/`**.
