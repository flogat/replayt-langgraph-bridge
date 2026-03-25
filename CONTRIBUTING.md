# Contributing to replayt-langgraph-bridge

## Development setup

1. Clone the repository
2. Install dependencies: `pip install -e .[dev]`
3. Run tests: `pytest`
4. Run linting: `ruff check src tests`

## Dependency management

### Adding or updating dependencies

1. Update `pyproject.toml` with the new dependency version
2. Run the supply-chain audit: `pip-audit --desc --severity-high`
3. If vulnerabilities are found:
   - Check if they affect your usage
   - Consider upgrading to a patched version
   - Document any accepted risks in `docs/DEPENDENCY_AUDIT.md`
4. Update the CI workflow if needed

### Running audits locally

