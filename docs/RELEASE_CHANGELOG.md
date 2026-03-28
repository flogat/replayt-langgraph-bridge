# Release notes and versioning (normative)

This document is the **maintainer-facing specification** for **`CHANGELOG.md`**, **compatibility signaling** (pins and public API), **Semantic Versioning** usage, and **how releases are cut** in this repository. It satisfies the product backlog **Establish CHANGELOG and compatibility signaling** and subsumes the earlier wording **Establish CHANGELOG and release versioning practice** (same artifacts and process).

**Related:** integrator-facing dependency rules are in **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md#dependency-and-pin-policy)**; contributor commands are in **[CONTRIBUTING.md](../CONTRIBUTING.md)**; coordinated disclosure, root **`SECURITY.md`**, and security-labeled changelog rules are in **[SECURITY_REPORTING_SPEC.md](SECURITY_REPORTING_SPEC.md)**.

---

## 1. Canonical artifacts

| Artifact | Role |
| -------- | ---- |
| **`CHANGELOG.md`** (repository root) | Human-readable history for packagers and integrators; **Keep a Changelog** style (see §2). |
| **`pyproject.toml`** **`[project].version`** | **Source of truth** for the string exposed as **`replayt_langgraph_bridge.__version__`** and for PyPI/metadata. Must match the version heading and tag for each published release (§5). |
| **Git tag** | Immutable pointer to the commit that released that version (§5). |

There is **no** separate changelog path; do not fragment history across multiple files.

---

## 2. Changelog format (Keep a Changelog)

Follow **[Keep a Changelog](https://keepachangelog.com/en/1.0.0/)** as already stated in **`CHANGELOG.md`**.

### Required structure

1. **`## [Unreleased]`** — **Must exist** at the top of the versioned sections. Accumulate noteworthy changes here until a release is cut. The section may be empty of bullets but the heading stays.
2. **Versioned sections** — **`## [X.Y.Z] - YYYY-MM-DD`** using **ISO 8601** dates for the **release day** (not the merge day of the last PR if different).
3. **Categories** — Use the standard groups (**Added**, **Changed**, **Deprecated**, **Removed**, **Fixed**, **Security**) where they add clarity. **Documentation** is acceptable as an additional grouping when a change is primarily normative docs that integrators should read before upgrading.

### Unreleased workflow (contributors)

1. **Land changes with notes** — In the **same pull request** as user-visible work, add one or more bullets under **`## [Unreleased]`** in **`CHANGELOG.md`** (see **[CONTRIBUTING.md](../CONTRIBUTING.md#changelog)** for what counts as user-visible).
2. **Group by category** — Place each bullet under the appropriate **###** subsection (**Added**, **Changed**, …). Prefer one bullet per coherent change; split large changes so packagers can scan quickly.
3. **Tie pins to the log** — Any edit to **`[project.dependencies]`**, **`requires-python`**, or moving packages between core and an optional extra must have a changelog bullet here (not only a **`pyproject.toml`** comment). Use **before → after** ranges or explicit new floors/ceilings (see below).
4. **At release time** — Maintainers move accumulated **Unreleased** content into a new dated **`## [X.Y.Z] - YYYY-MM-DD`** section per §5, then leave **Unreleased** in place (empty is fine).
5. **Headings always present** — The **`## [Unreleased]`** heading must remain even when there are no pending bullets.

### Dependency and compatibility signaling

When a change is **user-visible for installs or upgrades**, call it out under **Unreleased** (and later under the release section):

- **Floor or ceiling** changes on **replayt**, **langgraph**, or **`requires-python`** (including new runtime dependencies or moving packages between core and an optional extra).
- **New or renamed** optional extras that affect `pip install` resolution.
- **Breaking** public API or documented behavior (bridge majors or intentional breaking minors per §4).

Use concrete ranges or **before → after** wording so downstream tools and humans can scan without opening diffs. Align narrative with **`README.md`** compatibility lines and **DESIGN_PRINCIPLES — Current dependency constraints**.

### Breaking and experimental API signaling

- **Breaking** — Any change to **documented** public behavior that requires integrator action (including exception type or stable `code` changes, removed or renamed symbols in **`__all__`**, or intentional semantic changes to **`compile_replayt_workflow`** / **`initial_bridge_state`** contracts) must be called out with a **Breaking** lead-in at the start of the bullet (after the list marker), e.g. `- **Breaking:** …`, or as a **### Changed** / **### Removed** sub-bullet that starts with **Breaking**. Point to migration notes in **API.md**, **README**, or a dedicated doc when non-trivial.
- **Experimental** — New symbols or behaviors labeled **experimental** per **[API.md](API.md#experimental-and-internal-normative-rules)** must use an **Experimental** lead-in in **Unreleased** (**Added** is typical) until promoted to the stable table; promotion should be noted in the changelog when the experimental label is dropped.

---

## 3. Semantic Versioning for this package

This project **adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)** as stated in **`CHANGELOG.md`**.

**Bridge-specific interpretation:**

- **MAJOR** — Breaking changes to **documented** public API (**`__all__`**, behavior promised in **API.md** / **README**), or intentional compatibility breaks that require integrator action.
- **MINOR** — Backward-compatible functionality (new public API, backward-compatible behavior, new optional extras that do not alter default installs).
- **PATCH** — Backward-compatible fixes (bug fixes, docs that do not change behavior, internal refactors with no integrator impact).

**Pre-1.0 (`0.y.z`):** SemVer still applies, but **MINOR** releases **may** ship breaking API or default-behavior changes when required by upstream or deliberate bridge evolution, provided **`CHANGELOG.md`** uses explicit **Breaking** / **Experimental** lead-ins as in §2. **PATCH** releases should remain non-breaking for the documented public surface. Downstream packagers should **pin** (`~=0.1`, upper bound, or lockfile) and read **`CHANGELOG.md`** before upgrading within **0.x**.

**Upstream majors (replayt / LangGraph)** often require bridge **code**, **pins**, and **tests**; the resulting bridge release may be MINOR or MAJOR depending on whether integrators must change code or constraints. Follow the **Compatibility Update** template and maintainer checklist in **DESIGN_PRINCIPLES.md**.

---

## 4. Initial `0.1.0` section

The **`## [0.1.0] - …`** section records the **first published line** of the package. It should name, at minimum:

- That this is the initial **PyPI / distribution** release (or equivalent publication story).
- The **declared runtime** dependency ranges and **Python** floor **as of that release** (or a pointer to **`pyproject.toml`** if ranges are unchanged and already summarized in **README**).

Later releases **do not** rewrite **`[0.1.0]`** except to fix factual errors.

---

## 5. Release process (high level, manual)

**Today:** There is **no** GitHub Actions workflow that publishes to **PyPI**. Maintainers perform releases **manually** (or with local tooling). The following is the **intended checklist**; automation may be added later without changing the meaning of version, tag, and changelog.

1. **Confirm green mainline** — **`pytest`** and **`ruff check src tests`** as in **CONTRIBUTING.md** / **`.github/workflows/ci.yml`** on the releasing branch.
2. **Finalize notes** — Move content from **`[Unreleased]`** into a new **`## [X.Y.Z] - YYYY-MM-DD`** section (or merge into that section if partially pre-written). Leave **`[Unreleased]`** in place, empty or with a short placeholder if needed.
3. **Security-labeled entries** — If the release ships **security fixes** or **material security-behavior changes**, confirm **`CHANGELOG.md`** uses a **`### Security`** block or clearly labeled bullets per **[SECURITY_REPORTING_SPEC.md](SECURITY_REPORTING_SPEC.md#31-when-to-add-security-impact-notes)** and **[CONTRIBUTING.md](../CONTRIBUTING.md#changelog)**.
4. **Bump version** — Set **`[project].version`** in **`pyproject.toml`** to **`X.Y.Z`** on the same commit as the changelog finalize (or a dedicated release commit immediately after).
5. **Tag** — Create an annotated Git tag **`vX.Y.Z`** (leading **`v`**) on the commit that carries the released **`pyproject.toml`** version and changelog section. Example: version **0.2.0** → tag **`v0.2.0`**.
6. **Publish** — Build and upload the distribution (e.g. **`python -m build`** then **`twine upload`**) per project maintainer credentials and PyPI project settings. **Out of scope for CI in this spec** until a workflow exists.

**Tag vs. PyPI:** The **tag** marks the **exact source revision**; **PyPI** (or another index) is the **artifact** integrators install. Both should correspond to the same **`X.Y.Z`**.

---

## 6. Product backlog — builder acceptance criteria

Treat the backlog item **Establish CHANGELOG and compatibility signaling** (same normative bar as **Establish CHANGELOG and release versioning practice**) as **satisfied** when all of the following are true:

| # | Criterion |
| --- | --- |
| A | **`CHANGELOG.md`** exists at the repo root, references **Keep a Changelog** and **SemVer**, includes **`## [Unreleased]`**, and includes a dated **`## [0.1.0]`** section consistent with §4 and **`pyproject.toml`**. The **initial** release section reflects **declared runtime pins and Python floor** at that version (as today: **replayt** / **langgraph** ranges and **`requires-python`**). |
| B | **`CONTRIBUTING.md`** tells contributors **when** to update **`CHANGELOG.md`**, links **this document**, and states that **dependency bound** changes and **breaking** / **experimental** API changes require explicit changelog treatment (see §2). |
| C | **`README.md`** points integrators to **`CHANGELOG.md`** for upgrade review and to **this document** for versioning, **compatibility signaling**, and the manual release overview. |
| D | **This document** is present under **`docs/`**, covers §2–§5 (including **Unreleased workflow**, **dependency / breaking / experimental** signaling, **pre-1.0** expectations, and release checklist), and stays aligned with **DESIGN_PRINCIPLES** dependency/changelog bullets. |
| E | **Pin drift is visible** — Any merge that changes **`pyproject.toml`** runtime constraints (**replayt**, **langgraph**, **`requires-python`**, or core vs optional extra placement) also updates **`CHANGELOG.md` — Unreleased** with a scannable bullet (**before → after** or explicit new bound), in the **same** change set when practical. |
| F | **Breaking changes are explicit** — Documented public API or behavior breaks use a **Breaking** lead-in (§2) so downstream `grep` / release review catches them without inferring from diffs alone. |
| G | **Experimental changes are explicit** — New experimental surface uses an **Experimental** lead-in until promoted, consistent with **API.md**. |

Optional follow-up (not required by the backlog): CI checks or release automation; if added, update §5 and **README** in the same change set.
