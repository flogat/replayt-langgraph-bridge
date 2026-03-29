# Compatibility Update — Python 3.13 in CI (issue body draft)

Maintainers: file a **Compatibility Update** issue from **[`.github/ISSUE_TEMPLATE/compatibility_update.md`](../.github/ISSUE_TEMPLATE/compatibility_update.md)** and paste the sections below, or reference this file from the implementing PR. This draft maps **[BACKLOG_PYTHON_313_CI_MATRIX.md](BACKLOG_PYTHON_313_CI_MATRIX.md)** **P1**–**P3** after the matrix change lands.

## Upstream Package Information

- **Package name**: CPython (interpreter)
- **New version**: 3.13.x
- **Release date**: (see [python.org](https://www.python.org/downloads/))
- **Release notes URL**: [What’s new in Python 3.13](https://docs.python.org/3/whatsnew/3.13.html)

### Python interpreter / CI matrix expansion

Normative backlog: **[BACKLOG_PYTHON_313_CI_MATRIX.md](BACKLOG_PYTHON_313_CI_MATRIX.md)**.

- [x] **Spike readiness** — **replayt**, **langgraph**, and **`[dev]`** tools (**pytest**, **ruff**, **mypy**, **uv** / **setup-uv** in **`.github/workflows/ci.yml`**) run on **3.13** in CI; no upstream blockers found for this bridge’s pinned ranges at rollout.
- [x] **`uv.lock`** — No resolver change required for this rollout: **`uv sync --frozen --extra dev`** succeeds on **3.13** with the committed lock (markers already distinguish deps where wheels/metadata differ by Python).
- [x] **pytest** — Full suite green on **3.13** (**`uv run pytest`**, no path/marker filter), matching job **`test`**.
- [x] **CI workflow** — **`.github/workflows/ci.yml`** includes **3.13** on **`test`** and **`supply-chain`**; **ruff**, **mypy**, and **pytest** (or **pip-audit**) steps match other matrix legs.
- [x] **Documentation** — **DESIGN_PRINCIPLES** **Tested matrix** row and **DEPENDENCY_LOCK_STRATEGY** §3.2 updated; **README** / **MISSION** / **REPLAYT_BOUNDARY_TESTS** CI lines list **3.13**.
- [x] **Quirks / notes (in this issue)** — See below.

## Test Results

- [x] Ran existing test suite against **3.13**
- [x] Test results: **green** (pytest, ruff, mypy) on **3.13** in local verification and CI
- [x] Breaking changes identified: **none** for this bridge at current **replayt** / **langgraph** pins

## Impact Assessment

- [x] Bridge functionality affected: **none**
- [x] API changes required: **none**
- [x] Documentation updates needed: **done** (policy + README/MISSION alignment)
- [x] Migration guide needed: **no**

## Required Changes

- [ ] Update dependency constraints in `pyproject.toml` — **N/A** (interpreter-only expansion)
- [x] Update compatibility matrix in documentation
- [x] Add new tests for changed behavior — **N/A**; added matrix contract test in **`tests/test_dependency_strategy.py`**
- [x] Update changelog

## Documentation Updates

- [x] Update `README.md` compatibility / CI section
- [x] Update `docs/DESIGN_PRINCIPLES.md` dependency constraints / tested matrix
- [x] Update version-specific documentation as needed (**MISSION**, **REPLAYT_BOUNDARY_TESTS**, **DEPENDENCY_AUDIT**)

## Quirks / notes

- **Lock markers:** **`uv.lock`** already records **Python-version-specific** dependency edges (for example **`typing-extensions`** only where **`python_full_version < '3.13'`** for some packages). That is expected; do not strip markers when regenerating the lock.
- **mypy:** **`[tool.mypy] python_version = "3.11"`** in **`pyproject.toml`** stays the **static analysis** baseline. CI still runs **`uv run mypy -p replayt_langgraph_bridge`** on each matrix leg; behavior matches the pre-**3.13** matrix approach.
- **pytest:** No new **skips** or **xfails** for **3.13**; the default suite passes without demo extras.
- **Supply chain:** **`pip-audit`** runs per matrix leg on the same frozen **`[dev]`** graph as **`test`**.

## Timeline & Priority

- **Priority**: Completed as backlog **Python 3.13 CI matrix readiness issue and policy hook**
- **Estimated effort**: (see merged PR)
- **Target release**: (bridge release when maintainers cut one)

## Notes

Link the GitHub issue you file here: `________________`
