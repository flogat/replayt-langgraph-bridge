# Compatibility Update — replayt 0.5 readiness (issue body draft)

Maintainers: file a **Compatibility Update** issue from **[`.github/ISSUE_TEMPLATE/compatibility_update.md`](../.github/ISSUE_TEMPLATE/compatibility_update.md)** with title like **`Compatibility: replayt 0.5.x`**, paste or adapt the sections below, and link **[`docs/BACKLOG_REPLAYT_05_READINESS.md`](BACKLOG_REPLAYT_05_READINESS.md)**.

## Upstream Package Information

- **Package name**: replayt
- **New version**: **0.5.x** (target line; use the concrete prerelease tag or GA when testing)
- **Release date**: (fill when upstream publishes **0.5** on PyPI)
- **Release notes URL**: (fill from upstream changelog / docs when available)

### Replayt 0.5+ compatibility (bridge consumer work)

Normative backlog: **[docs/BACKLOG_REPLAYT_05_READINESS.md](BACKLOG_REPLAYT_05_READINESS.md)**.

- [x] **API inventory** — See **§ API inventory (R2)** below; reconciled against **replayt 0.4.25** (current PyPI latest). Re-validate against **0.5** release notes when a candidate exists.
- [x] **Boundary tests** — **§1 unchanged** for this milestone: no new replayt symbols are required until **0.5** API and release notes are available; bridge still uses **`Workflow`**, **`Runner`**, **`RunContext`**, **`JSONLStore`**, and **`RunResult`** (tests only) as in **[docs/REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md) §1**.
- [x] **Pin decision** — **`pyproject.toml`** stays **`replayt>=0.4.0,<0.5`** until a published **0.5.x** (or approved prerelease) passes **`uv sync --frozen --extra dev`** and **`uv run pytest`** on **Python 3.11–3.13** (see **R3** / **R4**).

## API inventory (R2)

| Location | `replayt.*` usage | Public / documented | 0.5 status (as of bridge PR) |
| -------- | ----------------- | ------------------- | ------------------------------ |
| **`src/replayt_langgraph_bridge/graph.py`** | `RunContext`, `Runner` (`replayt.runner`); `Workflow` (`replayt.workflow`) | Yes — core workflow/run API | **TBD** when **0.5** notes ship |
| **`tests/test_replayt_boundary_contracts.py`** | `replayt` (package), `JSONLStore`, `RunResult`, `Runner`, `Workflow` | Yes | **TBD** |
| **`tests/test_bridge_graph.py`**, **`test_state_payload_validation.py`**, **`test_log_redaction.py`**, **`test_security_threat_model.py`**, **`test_disk_checkpoint_sqlite_roundtrip.py`** | `JSONLStore`, `Runner`, `Workflow` | Yes | **TBD** |
| **`tests/test_large_graph_compile_advisory.py`** | `Workflow` | Yes | **TBD** |

Nothing in **`src/`** imports undocumented **`replayt._*`** modules.

## Test Results

- [x] Ran existing test suite against **replayt 0.4.x** (locked **`[dev]`** graph): **green** locally with **`uv sync --frozen --extra dev`** and **`uv run pytest`**.
- [ ] Ran suite against **replayt 0.5.x** — **blocked**: no **0.5** release on PyPI yet (see **R4**).
- [x] Breaking changes identified for **0.5**: **unknown** until upstream publishes the line.

## Impact Assessment

- [x] Bridge functionality affected by **0.5**: **TBD** after candidate install.
- [x] API changes required: **TBD** (inventory above is the watch list).
- [x] Documentation updates needed: **yes** when the pin widens — **`pyproject.toml`**, **README**, **DESIGN_PRINCIPLES**, **CHANGELOG**, **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** if §1 changes.
- [x] Migration guide needed: **TBD** after upstream breaking notes.

## Required Changes

- [ ] Update dependency constraints in `pyproject.toml` — **defer** until **0.5** is installable and CI-green (plan: **`>=0.5.0,<0.6`** mirroring the **0.4.x** pattern, unless upstream requires a different floor).
- [x] Update compatibility matrix in documentation — **pointer added**: this draft + **BACKLOG_REPLAYT_05_READINESS**; full matrix edit on pin widen.
- [x] Add new tests for changed behavior — **disk SQLite test** collection fixed without **`[dev]`** (`pytest.importorskip` for **`langgraph.checkpoint.sqlite`**); replayt-facing behavior unchanged.
- [ ] Update changelog — **when** **`replayt`** range changes (**CONTRIBUTING** / **R3**).

## Documentation Updates

- [x] **`docs/COMPATIBILITY_UPDATE_REPLAYT_05.md`** (this draft) and **[`docs/BACKLOG_REPLAYT_05_READINESS.md`](BACKLOG_REPLAYT_05_READINESS.md)** linked from **[`docs/REPLAYT_BOUNDARY_TESTS.md`](REPLAYT_BOUNDARY_TESTS.md)** (**Related documents**).
- [x] **`docs/DESIGN_PRINCIPLES.md`** — **Current dependency constraints** note for **0.5** tracking.
- [ ] **`README.md`** — refresh **replayt** compatibility line when the pin moves past **`<0.5`**.

## R4 — Green CI or documented blockers

**Blocker (upstream availability):** PyPI’s published **`replayt`** versions (see **[https://pypi.org/project/replayt/#history](https://pypi.org/project/replayt/#history)**) top out at **0.4.x** as of the implementing PR. There is no **0.5** wheel or sdist to run **`uv lock`** / matrix tests against.

**Next step:** When **replayt 0.5** (prerelease or GA) appears on PyPI, install it explicitly (branch or override), run **`uv run pytest`** on **3.11–3.13**, regenerate **`uv.lock`** if the range widens, and replace this **R4** section in the filed GitHub issue with paste links to CI runs or logs.

## Timeline & Priority

- **Priority**: Tracked under Mission Control **`8c5e0a89-66d8-4e11-ac7e-532b39f11156`** (**Replayt 0.5 readiness checklist and boundary test updates**).
- **Estimated effort**: Pin widen + test/doc pass after **0.5** publish.
- **Target release**: Bridge release when maintainers adopt **0.5** support.

## Notes

Link the GitHub issue you file here: `________________`
