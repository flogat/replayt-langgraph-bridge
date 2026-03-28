# Security reporting and security-relevant release notes (normative spec)

This document is the **builder-facing specification** for coordinated vulnerability reporting and for how security-impacting work surfaces in release notes. It satisfies backlog **Define a security changelog and vulnerability reporting channel** (phase **2** spec). Phase **3** implements the user-facing **`SECURITY.md`** at the repository root and aligns maintainer docs with this spec.

## 1. Goals

- Give downstream adopters a **private** channel to report security issues in **`replayt-langgraph-bridge`** (this package), with clear steps and honest scope.
- Ensure **security-relevant fixes and advisories** are reflected in **`CHANGELOG.md`** in a predictable way.
- Avoid implying **formal certification**, compliance guarantees, or SLA-backed security programs this project does not run.

## 2. Deliverable: root `SECURITY.md`

**Location:** repository root, filename exactly **`SECURITY.md`** (GitHub surfaces this for the **Security** tab and community expectations).

**Audience:** reporters, integrators, and security teams skimming the repo.

### 2.1 Required sections (builder checklist)

| Section | Must include |
| -------- | -------------- |
| **How to report** | Prefer **private** reporting **before** public disclosure. Acceptable patterns: (a) **GitHub Security Advisories** / **private vulnerability reporting** for this repository if enabled by maintainers, and/or (b) a **dedicated security contact email** maintained by the project. State **one primary** method and fallbacks if any. Explicitly ask reporters **not** to file public issues with exploit details. |
| **What to include** | Encourage: affected versions, reproduction steps or proof-of-concept **without** weaponization, impact assessment, and contact for follow-up. |
| **Supported versions** | Honest **supported version policy** for **this package** (e.g. **pre-1.0**, **best-effort** security fixes on the latest release line, or explicit “only the latest patch release”). Must align with **`pyproject.toml`** / **`README.md`** compatibility language; may defer **upstream** (replayt, LangGraph) security posture to those projects with links where appropriate. |
| **Response expectations** | **Non-binding** acknowledgment timeline (e.g. “we aim to acknowledge within a few business days”) and that timelines depend on severity and maintainer availability—**not** a contractual SLA. |
| **Disclosure** | Coordinated disclosure intent: maintainers work with reporters toward a release or advisory; avoid premature public technical detail when a fix is pending. |
| **Scope** | Clarify this policy covers **vulnerabilities in this bridge package** as published; integrator application code, custom checkpointers, and **replayt** / **LangGraph** runtime issues may belong elsewhere (with pointers to **[THREAT_MODEL.md](THREAT_MODEL.md)** and upstream trackers as needed). |

### 2.2 Required prohibitions (must not appear in `SECURITY.md`)

- No claims of **SOC 2**, **ISO 27001**, **FIPS**, **FedRAMP**, or other **formal certification** programs unless the project has actually achieved them (default: **do not** claim any).
- No promise of **bug bounty**, **paid support**, or **guaranteed** patch windows unless explicitly true.

### 2.3 Cross-links (recommended in `SECURITY.md`)

- **[docs/THREAT_MODEL.md](THREAT_MODEL.md)** — checkpoint/state trust boundaries and non-goals.
- **[docs/DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** — secrets policy and dependency/supply-chain notes.
- **[CHANGELOG.md](../CHANGELOG.md)** — where security fixes are recorded for releases.

## 3. Changelog and release process

### 3.1 When to add security impact notes

Maintainers **must** add a **`CHANGELOG.md`** entry under **`[Unreleased]`** (or the release section when tagging) when a change:

- **Fixes a vulnerability** in this package (CVE, GHSA, or internal severity), or
- **Materially changes** documented security behavior (e.g. validation limits, redaction defaults, trust-boundary docs) in a way integrators must react to.

Use a **`Security`** subsection under the release (Keep a Changelog style) or clearly labeled bullets (e.g. prefix **Security:**) so scanners and humans can find them.

### 3.2 What to write

- **User-visible** impact: what integrators should do (upgrade, config change, avoid pattern X).
- **Credit** when appropriate (reporter or identifier) without embedding exploit walkthroughs in the changelog body; link to an advisory if one exists.

### 3.3 Relationship to `SECURITY.md`

- **`SECURITY.md`** explains **how to report** and **what is supported**.
- **`CHANGELOG.md`** records **what shipped** for each version, including security fixes.

## 4. Where this is enforced in maintainer docs

- **`CONTRIBUTING.md`** — release/changelog expectations for security notes (normative for contributors).
- **`docs/DESIGN_PRINCIPLES.md`** — references this spec under security-related references.

## 5. Builder acceptance criteria (phase 3)

Treat the backlog as **done** when:

1. Root **`SECURITY.md`** exists and satisfies **§2.1** and **§2.2**.
2. **`CONTRIBUTING.md`** includes a **Releases / changelog / security** subsection consistent with **§3** (may be a short summary pointing here).
3. **`CHANGELOG.md`** documents the introduction of **`SECURITY.md`** and any process change under **Unreleased** when the Builder lands the files.
4. **`README.md`** or **`docs/MISSION.md`** links adopters to **`SECURITY.md`** for reporting (one clear pointer is enough).

Optional follow-up (not required for backlog closure): GitHub **Security policy** enabled in repo settings to match the documented channel.
