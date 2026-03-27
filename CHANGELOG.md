# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Bridge-originated structured logging on logger `replayt_langgraph_bridge` (`LogRecord.replayt_bridge`) with default key/pattern redaction, optional `RedactorHook`, `REPLAYT_BRIDGE_STRICT_REDACT` / `strict_redact`, and `redact=False` escape hatch (warning). Wired from `compile_replayt_workflow` (`src/replayt_langgraph_bridge/redaction.py`, `bridge_log.py`, `graph.py`); tests in `tests/test_log_redaction.py`.
- Tests that lock the **dependency policy** to **`pyproject.toml`** (runtime vs **`dev`** extra) and assert the **Compatibility Update** issue template is present (`tests/test_dependency_strategy.py`).
- Added matrixed `supply-chain` CI job (`pip-audit --ignore-vuln CVE-2026-4539 --desc`) that scans runtime and dev dependencies across Python 3.11/3.12 (PyPA `pip-audit` has no `--severity-high` flag; ignore documented in `docs/DEPENDENCY_AUDIT.md`).
- Secrets policy for LLM and tool integrations, covering environment-backed configuration, key rotation, safe/anti-patterns, and tracing considerations (`docs/DESIGN_PRINCIPLES.md`).

### Documentation

- Normative **log redaction** spec for bridge-originated structured logs: default key deny list, value patterns, strict mode (`REPLAYT_BRIDGE_STRICT_REDACT`), integrator hook contract, scope/non-goals, and builder acceptance criteria (**[docs/LOG_REDACTION.md](docs/LOG_REDACTION.md)**); cross-links from **DESIGN_PRINCIPLES**, **THREAT_MODEL**, **MISSION**, and **README**.
- Refined **dependency and pin policy**: minimum supported vs upper bounds vs CI behavior, optional **`dev`** extra, justified runtime constraints, LangGraph major rollout risk, and builder-facing acceptance criteria (`docs/DESIGN_PRINCIPLES.md`); aligned **README** dependency strategy and **CONTRIBUTING** pointers to the policy and **Compatibility Update** issue template.

## [0.1.0] - 2026-03-25

### Added

- Initial scaffold and package layout.
