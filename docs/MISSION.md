# Mission: LangGraph adapter mapping replayt workflow states to graph nodes and checkpoints

This repository is a **framework bridge**: it connects **replayt workflows** to **LangGraph** so integrators can express replayt-backed execution as a graph (nodes, edges, checkpoints) without re-implementing replayt semantics.

## Users and problem

| Who | Need |
| --- | --- |
| **Integrators** | Run durable replayt workflows inside LangGraph with a documented, versioned boundary. |
| **Maintainers** | Own pins, shims, and tests when replayt or LangGraph releases change behavior. |

**Problem this removes:** One-off glue between replayt's workflow/checkpoint model and LangGraph; unclear ownership when either stack moves, and no shared place for compatibility policy or automated checks.

## Replayt's role

- **In scope of replayt (upstream):** Workflow state, persistence/checkpointing primitives, and the execution contracts replayt exposes as public API. This adapter **consumes** those capabilities; it is **not** a fork of replayt.
- **Consumer-side (this repo):** Declaring and updating **version pins**, **compatibility shims**, LangGraph API drift, CI/test matrices, and release notes for the bridge. We do not expect replayt core to absorb LangGraph-specific details.

## Owned scope vs delegated work

| This package owns | Delegated upstream |
| ----------------- | ------------------ |
| Bridge API surface, docs, and tests for the integration boundary | Replayt core behavior and release cadence |
| Pins and changelog entries for `replayt-langgraph-bridge` | LangGraph runtime internals and roadmap |
| CI that runs automated tests for claimed behavior | Feature requests that belong in replayt or LangGraph issue trackers |

Upstream changes are tracked with tests and noted in the changelog when they affect integrators; proposals to core live in normal upstream channels (see **[DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)**).

## Success metrics

1. **Documented compatibility baseline** — Initial integration targets **replayt 0.4.x** and **LangGraph 1.1.x**; declared dependency ranges live in **`pyproject.toml`** and may widen as CI proves compatibility across patch releases.
2. **Automated tests in CI** — Unit and boundary tests for behavior we document; CI fails on regressions with clear logs (see **[DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)**). GitHub Actions workflow **[`.github/workflows/ci.yml`](../.github/workflows/ci.yml)** runs job **`test`** (Python **3.11** and **3.12** matrix) with **`pytest`**, matching the local command in the README.
3. **Small, explicit public surface** — Narrow APIs and documented extension points so integrators can depend on stable contracts.

**Runtime:** Python **3.11+** (`requires-python` in `pyproject.toml`).

## Security Considerations

For security considerations regarding checkpoint and state data, see **[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)**. For the planned contract for **bridge-originated log redaction** (deny lists, patterns, strict mode, extension hook), see **[docs/LOG_REDACTION.md](docs/LOG_REDACTION.md)**.
