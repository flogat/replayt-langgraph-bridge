# Dependency Audit Log

This document tracks supply-chain vulnerabilities that have been identified and assessed for the replayt-langgraph-bridge project.

## Audit Process

All dependencies are scanned using **`uv run pip-audit --ignore-vuln CVE-2026-4539 --desc`** in the CI pipeline (`supply-chain` job), after the same **`uv sync --frozen --extra dev`** step as the **`test`** job. The PyPA tool does not support a `--severity-high` filter; any reported vulnerability fails the job except CVEs explicitly ignored here and mirrored in the workflow.

**Locked resolution:** `pip-audit` runs in the **same frozen `[dev]` environment** as **`test`** (**`uv run`** after **`uv sync --frozen --extra dev`**), so reported CVEs match the committed **`uv.lock`** graph. Security alert handling, lock regeneration, and **SLA-style** triage for **`supply-chain`** failures are mapped in **[DEPENDENCY_LOCK_STRATEGY.md](DEPENDENCY_LOCK_STRATEGY.md)** §6 (including **[pip-audit / `supply-chain` job failure triage](DEPENDENCY_LOCK_STRATEGY.md#pip-audit--supply-chain-job-failure-triage-maintainer-playbook)**).

## Current Status

**Last audit**: 2026-03-26 — supply-chain job green with documented ignore for transitive **pygments** advisory below.  
**Status**: Runtime + dev tree monitored; one accepted transitive risk documented.

## Vulnerability Assessment Framework

When vulnerabilities are reported, we assess them based on:

1. **Exploitability**: How easily can the vulnerability be triggered in our usage context?
2. **Impact**: What would be the consequences if exploited?
3. **Mitigation**: Are there workarounds or patches available?
4. **Timeline**: When can we upgrade to a patched version?

## Accepted Risks

### CVE-2026-4539 — pygments (transitive)

- **Package**: `pygments` (e.g. 2.19.x pulled transitively via **replayt → typer → rich → pygments**).
- **Issue**: ReDoS in **AdlLexer** (not used by this package’s code paths or CI beyond importing the dependency stack).
- **Mitigation**: Track upstream **pygments** / **rich** / **replayt** releases; remove `--ignore-vuln` from `.github/workflows/ci.yml` when the resolved tree includes a fixed version.
- **CI**: `.github/workflows/ci.yml` uses **`uv run pip-audit --ignore-vuln CVE-2026-4539 --desc`** so the job matches this documented acceptance.

## History

### LangGraph 1.2.x compatibility spike (backlog `ad68b829`)

**Spec:** **[BACKLOG_LANGGRAPH_12_COMPATIBILITY_SPIKE.md](BACKLOG_LANGGRAPH_12_COMPATIBILITY_SPIKE.md)**.

**Spike date:** 2026-03-29 (builder phase **3**).

#### Upstream versions exercised

Resolved graph from **`uv sync --frozen --extra dev`** / **`uv.lock`** on PyPI (builder container, Python **3.12**):

| Package | Version |
| ------- | ------- |
| **langgraph** | **1.1.3** |
| **langgraph-checkpoint** | **4.0.1** |
| **langgraph-prebuilt** | **1.0.8** |
| **langgraph-sdk** | **0.3.12** |
| **langgraph-checkpoint-sqlite** (**`[dev]`** only) | **3.0.3** |

**No `langgraph` 1.2.x** sdist or wheel was available on PyPI on this date (`pip index versions langgraph` listed **1.1.3** as latest). The upstream **langgraph** repo **`libs/langgraph/pyproject.toml`** on **`main`** still declared version **1.1.3**, so there was no separate **1.2** line to install from Git for this spike without tracking an unmerged branch.

#### §2 touchpoint inventory (baseline on 1.1.3; 1.2-specific drift **unknown** until a 1.2 artifact exists)

| §2 area | Verdict | Evidence |
| ------- | ------- | -------- |
| **2.1** `compile_replayt_workflow` / graph build (imports, `StateGraph` generics, `compile(..., checkpointer=, interrupt_*=)`, node `Runtime` / `runtime.context`, routing + `END`) | **compatible** (on **1.1.3**) | **`tests/test_bridge_graph.py`** (all passed); **`tests/test_large_graph_compile_advisory.py`** |
| **2.2** `BridgeValidatingCheckpointSaver` / saver delegation | **compatible** (on **1.1.3**) | **`tests/test_bridge_graph.py`** (`MemorySaver`); **`tests/test_disk_checkpoint_sqlite_roundtrip.py`** (`SqliteSaver`); **`tests/test_state_payload_validation.py`** |
| **2.3** `langgraph.checkpoint.base` types + `RunnableConfig` boundary | **compatible** (on **1.1.3**) | Imports in **`replayt_langgraph_bridge.state_validation`**; checkpoint validation tests above |
| **2.4** `invoke` / `config["configurable"]["thread_id"]` / `context={"runner": ...}` / resume `invoke(None, ...)` | **compatible** (on **1.1.3**) | **`tests/test_bridge_graph.py`** (`MemorySaver`, interrupt before/after) |
| **1.2.x (future)** | **unknown** | Re-run when **1.2.x** appears on PyPI (or an agreed pre-release); compare failures to **§2** rows |

#### Test signal (CI parity trio)

| Command | Result |
| ------- | ------ |
| **`uv run pytest`** (no path filter) | **135 passed**, exit code **0** |
| **`uv run ruff check src tests`** | clean, exit code **0** |
| **`uv run mypy -p replayt_langgraph_bridge`** | success, exit code **0** |

**Primary oracle** **`tests/test_bridge_graph.py`:** all tests **passed**. **Secondary oracle** **`tests/test_disk_checkpoint_sqlite_roundtrip.py`:** **passed** with **`[dev]`** and **`langgraph-checkpoint-sqlite`** (phase **1c** collection **ERROR** matches an install without that dev graph / lock sync, not a missing spec).

#### Shim strategy

- Prefer **narrow code changes** in **`graph.py`** / **`state_validation.py`** when public LangGraph APIs move; avoid reliance on undocumented internals.
- If drift is **typing-only**, use **`typing.TYPE_CHECKING`** or targeted annotations compatible with **`mypy -p replayt_langgraph_bridge`**.
- **Not** recommended: pinning to arbitrary Git **main** revisions for releases; **runtime** version branches keyed on unreleased semver.

#### Pin / SemVer decision

- **Hold** **`langgraph>=1.1.0,<1.2`** until a **published** **1.2.x** (or maintainer-agreed candidate) is run through **full** **`pytest`**, **`ruff`**, and **`mypy`** on an updated **`uv.lock`**.
- When **1.2.x** is **green**: widen to **`>=1.1.0,<1.3`** in a **semver-minor** bridge release, updating **`pyproject.toml`**, **`uv.lock`**, **README**, **DESIGN_PRINCIPLES** (**Current dependency constraints**), and **CHANGELOG** in one change set (**LG12-A4**–**A5**); touch **CHECKPOINT_PERSISTENCE** §7 / **API.md** only if integrator-visible **invoke** or interrupt semantics change (**LG12-A6**).
- **Bridge major** is **not** indicated by this spike alone; treat **1.2** as the next **minor** within LangGraph **1.x** until evidence requires a stronger bump (**DESIGN_PRINCIPLES** — **Rollout risk for LangGraph majors**).

### Initial Setup
- Added `pip-audit` to CI workflow
- Created dependency audit documentation
- No vulnerabilities detected in initial dependency set (dev-only)

### Runtime Dependencies Added
- Added `replayt>=0.4.0,<0.5` and `langgraph>=1.1.0,<1.2`
- CI `pip-audit` passed (no reported vulnerabilities)
- Matches compatibility matrix in `docs/DESIGN_PRINCIPLES.md`

### Phase 3 - CI Enhancement
- Matrixed `supply-chain` job across Python 3.11, 3.12, and 3.13
- Confirmed clean `pip-audit --desc` runs (no reported vulnerabilities at the time)
- Completed `CONTRIBUTING.md` dependency management docs

### Reproducible lock (Backlog e41a2c55)

- Committed root **`uv.lock`** for the **`[dev]`** surface (**no** **`demo`**).
- **`test`** and **`supply-chain`** use **`uv sync --frozen --extra dev`** then **`uv run`**; **`pip-audit`** scans that same environment.

### Supply-Chain Gates Spec (Backlog 591f8168)
- Retroactively documented for existing runtime deps (already clean per CI).
- Threshold: any reported vulnerability fails CI (`pip-audit --desc`; PyPA tool has no severity filter flag).
- Noise handling: Assessed/documented here if accepted.
- Bump process: CONTRIBUTING.md + local/CI audits + DESIGN_PRINCIPLES.md policy.

## Dependency Inventory

**Runtime dependencies** (pinned per compatibility policy):
- `replayt>=0.4.0,<0.5`
- `langgraph>=1.1.0,<1.2`

**Dev dependencies**:
- `pytest>=8.0`
- `ruff>=0.6.0`
- `pip-audit>=2.7.0`
- `mypy>=1.11.0`
- `langgraph-checkpoint-sqlite>=2.0.0` (disk checkpoint round-trip test only)
