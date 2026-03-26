# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added matrixed `supply-chain` CI job (`pip-audit --ignore-vuln CVE-2026-4539 --desc`) that scans runtime and dev dependencies across Python 3.11/3.12 (PyPA `pip-audit` has no `--severity-high` flag; ignore documented in `docs/DEPENDENCY_AUDIT.md`).
- Secrets policy for LLM and tool integrations, covering environment-backed configuration, key rotation, safe/anti-patterns, and tracing considerations (`docs/DESIGN_PRINCIPLES.md`).

## [0.1.0] - 2026-03-25

### Added

- Initial scaffold and package layout.
