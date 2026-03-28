# Contributing to replayt-langgraph-bridge

## Development setup

1. Clone the repository
2. Install dependencies: `pip install -e .[dev]`
3. Run tests: `pytest`
4. Run linting: `ruff check src tests`

Integration-style tests that call **replayt** should follow **[docs/REPLAYT_BOUNDARY_TESTS.md](docs/REPLAYT_BOUNDARY_TESTS.md)** (contract-named assertions, `pytest.raises` `match=` strings, skip reasons with tracking issues).

When adding or renaming symbols intended for integrators, update **`replayt_langgraph_bridge.__all__`**, **[docs/API.md](docs/API.md)**, the **Public API** section of **README.md**, and **`tests/test_public_api.py`** (`_STABLE_PUBLIC_NAMES`) together (see **API.md** for the checklist).

## Dependency management

### Adding or updating dependencies

1. Update `pyproject.toml` with the new dependency version
2. Run the supply-chain audit (same flags as CI): `pip-audit --ignore-vuln CVE-2026-4539 --desc`
3. If vulnerabilities are found:
   - Check if they affect your usage
   - Consider upgrading to a patched version
   - Document any accepted risks in `docs/DEPENDENCY_AUDIT.md`
4. Update the CI workflow if needed

For **how** pins, ranges, and optional extras are chosen—and what “minimum supported” vs “what CI runs” means—see **[docs/DESIGN_PRINCIPLES.md#dependency-and-pin-policy](docs/DESIGN_PRINCIPLES.md#dependency-and-pin-policy)**. For **LLM vendor SDKs** and the optional **`demo`** extra, follow **[Core vs demo extras](docs/DESIGN_PRINCIPLES.md#core-vs-demo-extras-llm-clients-and-supply-chain)**—declare those packages only under `[project.optional-dependencies] demo`, never `[project.dependencies]`.

### Upstream compatibility (replayt / LangGraph majors)

When triaging a new **major** or a risky range change, open a **Compatibility Update** issue using **[`.github/ISSUE_TEMPLATE/compatibility_update.md`](.github/ISSUE_TEMPLATE/compatibility_update.md)** and follow the maintainer checklist in **DESIGN_PRINCIPLES.md** (same section as above).

### Running audits locally

To check for vulnerabilities in dependencies, run:

