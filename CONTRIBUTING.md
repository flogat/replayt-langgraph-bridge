# Contributing to replayt-langgraph-bridge

## Development setup

1. Clone the repository
2. Install **[uv](https://docs.astral.sh/uv/getting-started/installation/)** (CI pins **0.11.2** in **`.github/workflows/ci.yml`** via **`astral-sh/setup-uv`**).
3. Install dependencies from the lockfile (same graph as CI):

   ```bash
   uv sync --frozen --extra dev
   ```

4. Run tests: `uv run pytest`
5. Run linting: `uv run ruff check src tests`

Use **`uv run pytest` with no extra paths or markers** for the integrator-relevant suite—the same invocation as the **`test`** job in **`.github/workflows/ci.yml`** after **`uv sync --frozen --extra dev`**. That run includes **contract-style replayt boundary** tests alongside other unit tests; see **[docs/REPLAYT_BOUNDARY_TESTS.md](docs/REPLAYT_BOUNDARY_TESTS.md)** for scope and the product backlog acceptance mapping.

**Without uv:** `pip install -e ".[dev]"` still works for a loose local tree, but it does not match CI’s frozen **`uv.lock`** graph.

## What must never be committed

Do **not** commit:

- **Secrets** — API keys, tokens, passwords, private keys, or any file whose primary purpose is holding them (for example **`.env`**, **`.env.local`**, raw **`*.pem`** / **`id_rsa`** private key material, or ad-hoc credential dumps). Cloud or OAuth tooling may use names such as **`application_default_credentials.json`**; never commit those into this tree—if your local workflow drops them next to the repo, add a **narrow** **`.gitignore`** rule per **[docs/GITIGNORE_AND_LOCAL_ARTIFACTS.md](docs/GITIGNORE_AND_LOCAL_ARTIFACTS.md)** (optional catalog and collision rules), not a catch-all that could hide tracked fixtures later. The same applies to copied **CLI or vendor credential files** (for example **`.netrc`**, **`.aws/credentials`**, or a **`gcloud`**-style application-default path) if they appear **under the repository tree**—prefer a documented subdirectory and a scoped ignore rule over broad `credentials` globs (**§6** in that doc).
- **Orchestration / agent scratch** — Paths under **`.orchestrator/`**, local agent skill trees such as **`.cursor/skills/`**, and similar tool output meant only for your machine (see **`.gitignore`** comments).
- **Local persistence experiments** — Checkpoint files, local SQLite DBs, or store dumps you create while developing graphs, unless the project explicitly chooses to track them as fixtures (today: keep them local or under a documented ignored directory).

Normative **`.gitignore`** categories, required exceptions for reproducible builds (**`uv.lock`**, **`pyproject.toml`**, **`src/`**, **`tests/`**, etc.), and verification commands: **[docs/GITIGNORE_AND_LOCAL_ARTIFACTS.md](docs/GITIGNORE_AND_LOCAL_ARTIFACTS.md)**. Representative ignore behavior is also checked by **`tests/test_gitignore_contract.py`** (**`git check-ignore`**); when you change **`.gitignore`** for a recurring footgun, update that test in the same change set per the spec (**G5**). For runtime secret handling and logging, see **[docs/DESIGN_PRINCIPLES.md#secrets-policy](docs/DESIGN_PRINCIPLES.md#secrets-policy)**.

Integration-style tests that call **replayt** must follow that document (contract-named assertions, `pytest.raises` `match=` strings, skip reasons with tracking issues).

When adding or renaming symbols intended for integrators, update **`replayt_langgraph_bridge.__all__`**, **[docs/API.md](docs/API.md)**, the **Public API** section of **README.md**, and **`tests/test_public_api.py`** (`_STABLE_PUBLIC_NAMES`) together (see **API.md** for the checklist).

## Dependency management

Normative policy and security→lock workflow: **[docs/DEPENDENCY_LOCK_STRATEGY.md](docs/DEPENDENCY_LOCK_STRATEGY.md)**. CI installs **`[dev]`** only from committed **`uv.lock`** (**`uv sync --frozen --extra dev`**); the optional **`demo`** extra is not part of that lock-driven install.

### Regenerating `uv.lock`

Run whenever **`pyproject.toml`** changes **`[project.dependencies]`**, **`[project.optional-dependencies]`**, or **`requires-python`** in a way that affects the **`[dev]`** install CI uses:

```bash
uv sync --extra dev
```

Omit **`--frozen`** so **`uv.lock`** updates. Commit **`pyproject.toml`** and **`uv.lock`** in the same change set. Use the same **uv** major/minor as CI when possible (**0.11.2** today).

### Adding or updating dependencies

1. Update `pyproject.toml` with the new dependency version
2. Regenerate the lock (commands above), then run the supply-chain audit (same flags as CI): `uv run pip-audit --ignore-vuln CVE-2026-4539 --desc`
3. If vulnerabilities are found:
   - Check if they affect your usage
   - Consider upgrading to a patched version
   - Document any accepted risks in `docs/DEPENDENCY_AUDIT.md`
4. Update the CI workflow if needed

For **how** pins, ranges, and optional extras are chosen—and what “minimum supported” vs “what CI runs” means—see **[docs/DESIGN_PRINCIPLES.md#dependency-and-pin-policy](docs/DESIGN_PRINCIPLES.md#dependency-and-pin-policy)**. For **LLM vendor SDKs** and the optional **`demo`** extra, follow **[Core vs demo extras](docs/DESIGN_PRINCIPLES.md#core-vs-demo-extras-llm-clients-and-supply-chain)**—declare those packages only under `[project.optional-dependencies] demo`, never `[project.dependencies]`.

### Upstream compatibility (replayt / LangGraph majors)

When triaging a new **major** or a risky range change, open a **Compatibility Update** issue using **[`.github/ISSUE_TEMPLATE/compatibility_update.md`](.github/ISSUE_TEMPLATE/compatibility_update.md)** and follow the maintainer checklist in **DESIGN_PRINCIPLES.md** (same section as above).

### Running audits locally

After **`uv sync --frozen --extra dev`** (or **`uv sync --extra dev`** if you are refreshing the lock), run:

```bash
uv run pip-audit --ignore-vuln CVE-2026-4539 --desc
```

Same flags as **`.github/workflows/ci.yml`** job **`supply-chain`**. Document accepted ignores in **`docs/DEPENDENCY_AUDIT.md`**.

## Changelog

When preparing a release or merging user-visible work:

1. Update **`CHANGELOG.md`** under **`[Unreleased]`** per [Keep a Changelog](https://keepachangelog.com/) (this project’s format is described at the top of that file).
2. **Security fixes or material security-behavior changes** (validation, redaction, trust boundaries) **must** be called out explicitly—use a **`Security`** subsection or clearly labeled bullets so adopters and scanners can find them. See **[docs/SECURITY_REPORTING_SPEC.md](docs/SECURITY_REPORTING_SPEC.md#3-changelog-and-release-process)**.
3. **Private vulnerability reports** must **not** be discussed in public issues before coordination; reporters should use root **[SECURITY.md](SECURITY.md)** (see **SECURITY_REPORTING_SPEC**).

Normative checklist for **`SECURITY.md`**, supported-version honesty, and changelog rules: **[docs/SECURITY_REPORTING_SPEC.md](docs/SECURITY_REPORTING_SPEC.md)**.

Update **[CHANGELOG.md](CHANGELOG.md)** in the **same pull request** as the change whenever the work is **user-visible**: public API or runtime behavior, **dependency floor or ceiling** on **replayt** / **langgraph** / **`requires-python`**, new or renamed optional extras, **security** fixes, or notable **normative doc** updates that integrators must follow (API, checkpoint, or validation contracts).

**Dependency pins** — Any change to declared runtime ranges or to which packages live in core vs an optional extra needs a changelog bullet with **before → after** (or explicit new bounds), not only a comment in **`pyproject.toml`**.

**Breaking and experimental API** — Follow **[docs/API.md](docs/API.md#experimental-and-internal-normative-rules)**. Changelog bullets must lead with **`Breaking:`** or **`Experimental:`** where applicable so packagers can scan releases without diff archaeology.

Purely internal refactors, test-only changes, or typo fixes that do not affect integrators **do not** require changelog entries unless they change documented behavior.

Formatting, **Unreleased** workflow (accumulate bullets, cut dated sections at release), **pre-1.0** SemVer expectations, compatibility signaling, and Git tag naming: **[docs/RELEASE_CHANGELOG.md](docs/RELEASE_CHANGELOG.md)**.

## Releases

Releases are **maintainer-driven** and **manual** today: there is **no** PyPI publish job in **`.github/workflows/`**. Version bump, changelog section, **`vX.Y.Z`** tag, and publish steps are specified in **[docs/RELEASE_CHANGELOG.md](docs/RELEASE_CHANGELOG.md)**.
