# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added matrixed `supply-chain` CI job (`pip-audit --desc --severity-high`) that scans runtime and dev dependencies across Python 3.11/3.12, failing on high-severity vulnerabilities.
- Secrets policy for LLM and tool integrations, covering environment-backed configuration, key rotation, safe/anti-patterns, and tracing considerations (`docs/DESIGN_PRINCIPLES.md`).

## [0.1.0] - 2026-03-25

### Added

- Initial scaffold and package layout.
