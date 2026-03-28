# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Replayt boundary tests in `tests/test_bridge_graph.py`: contract-named assertion messages, `pytest.raises` `match=` strings, and docstrings aligned with **[docs/REPLAYT_BOUNDARY_TESTS.md](docs/REPLAYT_BOUNDARY_TESTS.md)** (backlog: actionable failure messages).

### Added

- **Inbound bridge state validation** (backlog: harden deserialization): limits and `bridge_state_schema_version` per `docs/STATE_PAYLOAD_VALIDATION.md`, `BridgeStateValidationError`, validation in `initial_bridge_state` and before each step’s `RunContext.data` update, and a wrapping checkpointer that validates merged `invoke` input before LangGraph persists it (INPUT and loop puts that include `__start__`). Implementation in `src/replayt_langgraph_bridge/state_validation.py`; tests in `tests/test_state_payload_validation.py`.
- Bridge-originated structured logging on logger `replayt_langgraph_bridge` (`LogRecord.replayt_bridge`) with default key/pattern redaction, optional `RedactorHook`, `REPLAYT_BRIDGE_STRICT_REDACT` / `strict_redact`, and `redact=False` escape hatch (warning). Wired from `compile_replayt_workflow` (`src/replayt_langgraph_bridge/redaction.py`, `bridge_log.py`, `graph.py`); tests in `tests/test_log_redaction.py`.
- Tests that lock the **dependency policy** to **`pyproject.toml`** (runtime vs **`dev`** extra) and assert the **Compatibility Update** issue template is present (`tests/test_dependency_strategy.py`).
- Added matrixed `supply-chain` CI job (`pip-audit --ignore-vuln CVE-2026-4539 --desc`) that scans runtime and dev dependencies across Python 3.11/3.12 (PyPA `pip-audit` has no `--severity-high` flag; ignore documented in `docs/DEPENDENCY_AUDIT.md`).
- Secrets policy for LLM and tool integrations, covering environment-backed configuration, key rotation, safe/anti-patterns, and tracing considerations (`docs/DESIGN_PRINCIPLES.md`).

### Documentation

- Normative **public adapter API** spec (phase 2 backlog **Define the public adapter API and module layout**): export set tied to ``__all__``, stable vs experimental rules, submodule layout for maintainers, cross-links from README, **DESIGN_PRINCIPLES**, **MISSION**, **CONTRIBUTING**, and package docstring (**[docs/API.md](docs/API.md)**).
- Normative **replayt boundary testing** spec (phase 2 backlog **Add replayt boundary tests with actionable failure messages**): integration-style test scope, replayt API surface used by the bridge, actionable assertion / `pytest.raises` message rules, skip/issue requirements, and builder checklist (**[docs/REPLAYT_BOUNDARY_TESTS.md](docs/REPLAYT_BOUNDARY_TESTS.md)**); cross-links from **DESIGN_PRINCIPLES**, **MISSION**, **README**, and **CONTRIBUTING**.
- Normative **inbound bridge state** spec (phase 2 backlog **Harden deserialization of replayt state mapped into LangGraph**): size/depth limits, optional `bridge_state_schema_version`, validation error surface, checkpoint non-mutation test obligations, and README/THREAT_MODEL/DESIGN_PRINCIPLES/MISSION cross-links (**[docs/STATE_PAYLOAD_VALIDATION.md](docs/STATE_PAYLOAD_VALIDATION.md)**). Docstrings on `initial_bridge_state` / `compile_replayt_workflow` and the package docstring point at the spec. **Builder phase 3** added the runtime validation module, public `BridgeStateValidationError`, README limits, and tests (`tests/test_state_payload_validation.py`).
- Normative **log redaction** spec for bridge-originated structured logs: default key deny list, value patterns, strict mode (`REPLAYT_BRIDGE_STRICT_REDACT`), integrator hook contract, scope/non-goals, and builder acceptance criteria (**[docs/LOG_REDACTION.md](docs/LOG_REDACTION.md)**); cross-links from **DESIGN_PRINCIPLES**, **THREAT_MODEL**, **MISSION**, and **README**.
- **Log redaction** spec refinement (phase 2 backlog): backlog-to-spec traceability table, concrete `LogRecord` / `replayt_bridge` emission contract, field vs pattern **traversal semantics** aligned with `redaction.py`, **verification obligations** for CI, and updated **MISSION** / **THREAT_MODEL** links (**[docs/LOG_REDACTION.md](docs/LOG_REDACTION.md)**).
- Builder (phase 3 backlog): **README** / **DESIGN_PRINCIPLES** state bridge log redaction is in use (not a future requirement); `apply_field_redaction` module docstrings aligned with traversal semantics; `tests/test_log_redaction.py` covers email pattern masking in attachments.
- Refined **dependency and pin policy**: minimum supported vs upper bounds vs CI behavior, optional **`dev`** extra, justified runtime constraints, LangGraph major rollout risk, and builder-facing acceptance criteria (`docs/DESIGN_PRINCIPLES.md`); aligned **README** dependency strategy and **CONTRIBUTING** pointers to the policy and **Compatibility Update** issue template.

## [0.1.0] - 2026-03-25

### Added

- Initial scaffold and package layout.
