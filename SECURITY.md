# Security policy

This file describes how to report security issues in the **`replayt-langgraph-bridge`** Python package (this repository). It is not a legal contract and does not describe a paid or certified security program.

## How to report

Report suspected vulnerabilities **privately** before public disclosure. Do **not** open a public GitHub issue, discussion, or pull request that includes exploit details, full weaponized reproduction steps, or live data from production systems.

**Primary channel (GitHub):** Submit a **private vulnerability report** for this repository:

- Open **[Security advisories](https://github.com/flogat/replayt-langgraph-bridge/security/advisories/new)** (same flow as **Security → Report a vulnerability** on the GitHub repo page).

Maintainers use that channel for coordinated disclosure. If the link returns an error because private reporting is disabled on a fork, use **Security** on the **canonical** published repository or another **private** channel the maintainers publish for this project.

## What to include

Helpful details:

- Affected **versions** or **commits** (and how you installed the package, if relevant).
- Steps to reproduce the issue, or a minimal proof-of-concept, **without** turning the report into an exploit write-up aimed at bystanders.
- Your assessment of **impact** (confidentiality, integrity, availability) at a high level.
- A **contact path** for follow-up questions (the advisory thread is enough when you use GitHub reporting).

## Supported versions

This project is **pre-1.0**. Security fixes and hardening land on a **best-effort** basis on the **latest release line** maintainers support, consistent with **`pyproject.toml`** and **[README.md](README.md)** (currently **replayt** 0.4.x and **LangGraph** 1.1.x as declared ranges, **Python** 3.11+). Older tags may not receive backports. Security posture of **replayt**, **LangGraph**, and other upstream dependencies is owned by those projects; follow their advisories and upgrade paths for issues outside this bridge package.

## Response expectations

Maintainers aim to **acknowledge** new private reports within **a few business days**. Investigation, severity judgment, and release timing depend on the issue, available time, and upstream factors. Nothing in this file is a **service-level agreement** or a promise of a specific fix date.

## Disclosure

The goal is **coordinated disclosure**: work with maintainers toward a fix, advisory, or documented mitigation before publishing technical details that would make exploitation easier. Avoid premature public posts with full exploit instructions while a fix is still pending.

## Scope

This policy covers **vulnerabilities in this bridge package** as published here (for example graph compilation, bridge state handling, and documented integration behavior).

**Typically out of scope for this repository** (report to the right owner instead):

- Bugs and security issues in **application code**, custom graphs, or integrator-owned **checkpointers** and stores.
- Issues that belong to **replayt** or **LangGraph** runtimes or their dependencies—use those projects’ security channels.

For checkpoint and state **trust boundaries** and non-goals of the bridge, see **[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)**.

## Related documentation

- **[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)** — trust boundaries and checkpoint/state considerations.
- **[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** — secrets handling and dependency notes.
- **[CHANGELOG.md](CHANGELOG.md)** — security-relevant fixes and release notes (see also **[docs/SECURITY_REPORTING_SPEC.md](docs/SECURITY_REPORTING_SPEC.md)** and **[docs/RELEASE_CHANGELOG.md](docs/RELEASE_CHANGELOG.md)**).
