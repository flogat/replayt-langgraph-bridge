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

Update **[CHANGELOG.md](CHANGELOG.md)** in the **same pull request** as the change whenever the work is **user-visible**: public API or runtime behavior, **dependency floor or ceiling** on **replayt** / **langgraph** / **`requires-python`**, new or renamed optional extras, **security** fixes, or notable **normative doc** updates that integrators must follow (API, checkpoint, or validation contracts).

**Dependency pins** — Any change to declared runtime ranges or to which packages live in core vs an optional extra needs a changelog bullet with **before → after** (or explicit new bounds), not only a comment in **`pyproject.toml`**.

**Breaking and experimental API** — Follow **[docs/API.md](docs/API.md#experimental-and-internal-normative-rules)**. Changelog bullets must lead with **`Breaking:`** or **`Experimental:`** where applicable so packagers can scan releases without diff archaeology.

Purely internal refactors, test-only changes, or typo fixes that do not affect integrators **do not** require changelog entries unless they change documented behavior.

Formatting, **Unreleased** workflow (accumulate bullets, cut dated sections at release), **pre-1.0** SemVer expectations, compatibility signaling, and Git tag naming: **[docs/RELEASE_CHANGELOG.md](docs/RELEASE_CHANGELOG.md)**.

## Releases

Releases are **maintainer-driven** and **manual** today: there is **no** PyPI publish job in **`.github/workflows/`**. Version bump, changelog section, **`vX.Y.Z`** tag, and publish steps are specified in **[docs/RELEASE_CHANGELOG.md](docs/RELEASE_CHANGELOG.md)**.
