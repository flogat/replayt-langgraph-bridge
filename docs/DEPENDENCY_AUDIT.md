# Dependency Audit Log

This document tracks supply-chain vulnerabilities that have been identified and assessed for the replayt-langgraph-bridge project.

## Audit Process

All dependencies are scanned using `pip-audit --desc --severity-high` in the CI pipeline. Any high-severity vulnerabilities will cause the CI to fail, preventing them from entering the codebase.

## Current Status

**Last audit**: Initial setup  
**Status**: No high-severity vulnerabilities detected in current dependencies.

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
- No vulnerabilities detected in initial dependency set

## Dependency Inventory

As of initial setup, the project has no runtime dependencies in `pyproject.toml`. The following dev dependencies are pinned:

- `pytest>=8.0`
- `ruff>=0.6.0`
- `pip-audit>=2.7.0`

When runtime dependencies are added (e.g., `replayt>=0.4.0,<0.5`, `langgraph>=1.1.0,<1.2`), they will be documented here with their audit status.
