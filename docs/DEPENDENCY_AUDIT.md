# Dependency Audit Log

This document tracks supply-chain vulnerabilities that have been identified and assessed for the replayt-langgraph-bridge project.

## Audit Process

All dependencies are scanned using `pip-audit --desc --severity-high` in the CI pipeline (`supply-chain` job). Any high-severity vulnerabilities will cause the CI to fail, preventing them from entering the codebase.

## Current Status

**Last audit**: CI baseline (no high-severity vulnerabilities detected).  
**Status**: Clean on runtime + dev dependencies.

## Vulnerability Assessment Framework

When vulnerabilities are reported, we assess them based on:

1. **Exploitability**: How easily can the vulnerability be triggered in our usage context?
2. **Impact**: What would be the consequences if exploited?
3. **Mitigation**: Are there workarounds or patches available?
4. **Timeline**: When can we upgrade to a patched version?

## Accepted Risks

*None currently documented.*

## History

### [Date] - Initial Setup
- Added `pip-audit` to CI workflow
- Created dependency audit documentation
- No vulnerabilities detected in initial dependency set (dev-only)

### [Date] - Runtime Dependencies Added
- Added `replayt>=0.4.0,<0.5` and `langgraph>=1.1.0,<1.2`
- CI `pip-audit` passed (no high-severity issues)
- Matches compatibility matrix in `docs/DESIGN_PRINCIPLES.md`

## Dependency Inventory

**Runtime dependencies** (pinned per compatibility policy):
- `replayt>=0.4.0,<0.5`
- `langgraph>=1.1.0,<1.2`

**Dev dependencies**:
- `pytest>=8.0`
- `ruff>=0.6.0`
- `pip-audit>=2.7.0`
