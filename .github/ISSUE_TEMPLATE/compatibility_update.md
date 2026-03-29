---
name: Compatibility Update
about: Track and manage compatibility with upstream package releases
title: 'Compatibility: [PACKAGE] [VERSION]'
labels: compatibility, upstream
assignees: ''
---

## Upstream Package Information
- **Package name**: 
- **New version**: 
- **Release date**: 
- **Release notes URL**: 

### Python interpreter / CI matrix expansion (e.g. 3.13)

Use this subsection when the tracked change is the **Python runtime** or **GitHub Actions `test` matrix** (not only a PyPI package bump). Normative backlog: **[docs/BACKLOG_PYTHON_313_CI_MATRIX.md](../../docs/BACKLOG_PYTHON_313_CI_MATRIX.md)**. **Python 3.13** rollout checklist and quirks archive: **[docs/COMPATIBILITY_UPDATE_PYTHON_313.md](../../docs/COMPATIBILITY_UPDATE_PYTHON_313.md)**.

- [ ] **Spike readiness** — **replayt**, **langgraph**, and **`[dev]`** tools (**pytest**, **ruff**, **mypy**, **uv** / **setup-uv**) are usable on the target Python minor, or blocking gaps are listed under **Quirks / notes** below with upstream links.
- [ ] **`uv.lock`** — Regenerated as needed so **`uv sync --frozen --extra dev`** succeeds on the new interpreter; lock diff reviewed in the PR.
- [ ] **pytest** — Full suite **green** on the new matrix member (**`uv run pytest`** with **no path/marker filter**, same contract as **`.github/workflows/ci.yml`** **`test`**).
- [ ] **CI workflow** — **`.github/workflows/ci.yml`** includes the new Python version on **`test`** (and **`supply-chain`** if it shares the same matrix); **ruff**, **mypy**, and **pytest** steps match existing matrix legs.
- [ ] **Documentation** — **`docs/DESIGN_PRINCIPLES.md`** **Tested matrix** row and **`docs/DEPENDENCY_LOCK_STRATEGY.md`** §3.2 updated; **README** compatibility lines updated if integrator-facing tested versions change.
- [ ] **Quirks / notes (in this issue)** — Any **stdlib** deprecations/removals, **typing** or tooling edge cases, **upstream** workarounds, **skips**/**xfails** (with tracking links). Do **not** rely on chat-only context for maintainer handoff.

## Test Results
- [ ] Ran existing test suite against new version
- [ ] Test results: 
- [ ] Breaking changes identified: 

## Impact Assessment
- [ ] Bridge functionality affected: 
- [ ] API changes required: 
- [ ] Documentation updates needed: 
- [ ] Migration guide needed: 

## Required Changes
- [ ] Update dependency constraints in `pyproject.toml`
- [ ] Update compatibility matrix in documentation
- [ ] Add new tests for changed behavior
- [ ] Update changelog

## Documentation Updates
- [ ] Update `README.md` compatibility section
- [ ] Update `docs/DESIGN_PRINCIPLES.md` dependency constraints
- [ ] Update any version-specific documentation

## Timeline & Priority
- **Priority**: 
- **Estimated effort**: 
- **Target release**: 

## Notes
[Any additional context, links, or considerations]
