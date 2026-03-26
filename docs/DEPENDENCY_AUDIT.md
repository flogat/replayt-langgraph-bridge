# Dependency Audit Log

This document tracks supply-chain vulnerabilities that have been identified and assessed for the replayt-langgraph-bridge project.

## Audit Process

All dependencies are scanned using `pip-audit --ignore-vuln CVE-2026-4539 --desc` in the CI pipeline (`supply-chain` job). The PyPA tool does not support a `--severity-high` filter; any reported vulnerability fails the job except CVEs explicitly ignored here and mirrored in the workflow.

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
- **CI**: `.github/workflows/ci.yml` uses `pip-audit --ignore-vuln CVE-2026-4539 --desc` so the job matches this documented acceptance.

## History

### Initial Setup
- Added `pip-audit` to CI workflow
- Created dependency audit documentation
- No vulnerabilities detected in initial dependency set (dev-only)

### Runtime Dependencies Added
- Added `replayt>=0.4.0,<0.5` and `langgraph>=1.1.0,<1.2`
- CI `pip-audit` passed (no reported vulnerabilities)
- Matches compatibility matrix in `docs/DESIGN_PRINCIPLES.md`

### Phase 3 - CI Enhancement
- Matrixed `supply-chain` job across Python 3.11/3.12
- Confirmed clean `pip-audit --desc` runs (no reported vulnerabilities at the time)
- Completed `CONTRIBUTING.md` dependency management docs

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
