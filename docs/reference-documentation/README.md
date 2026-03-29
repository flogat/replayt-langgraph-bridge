# Reference documentation (replayt and LangGraph)

Optional, maintainer-curated pointers for **replayt** and **LangGraph** context used by **replayt-langgraph-bridge**. This folder does **not** replace upstream documentation; upstream sources remain authoritative.

Normative backlog spec and acceptance IDs (**R1–R9**): **[`docs/BACKLOG_REFERENCE_DOCUMENTATION.md`](../BACKLOG_REFERENCE_DOCUMENTATION.md)** (Mission Control `0867a72f-8b61-4a00-b076-ddb45cd1b7c8`).

## Pin alignment

- **Declared ranges** for runtime dependencies come from **`pyproject.toml`** **`[project.dependencies]`**: **replayt** `>=0.4.0,<0.5`, **langgraph** `>=1.1.0,<1.2`.
- **Exact patch versions** used in maintainer and CI workflows come from the root **`uv.lock`** when you run **`uv sync --frozen --extra dev`**. Those resolved versions can differ from “latest in range” at any moment; regenerate the lock after dependency changes per **CONTRIBUTING** and **[`docs/DEPENDENCY_LOCK_STRATEGY.md`](../DEPENDENCY_LOCK_STRATEGY.md)**.

## Refresh cadence

Update **`links.manifest.json`** (and this **`README`** if the pin story changes) **whenever**:

- **`pyproject.toml`** bounds for **replayt** or **langgraph** change, or
- **`uv.lock`** is regenerated for a **compatibility-related** reason (security refresh, intentional bump, CI lock drift fix).

Maintainers may also do a **quarterly** pass over manifest URLs to fix obvious breakage; that is optional and does not replace bump-driven updates.

## Licensing and format

- **Canonical upstream URLs** live in **`links.manifest.json`**. Each entry includes **`pin_note`** and **`last_reviewed`** (see **[`docs/BACKLOG_REFERENCE_DOCUMENTATION.md`](../BACKLOG_REFERENCE_DOCUMENTATION.md)** **R6**).
- **LangGraph** and **LangChain** web documentation is linked, not copied here, so we avoid redistributing full vendor doc trees under unclear terms.
- **`bridge-integration-notes.md`** is **first-party** text (no upstream prose). It is a short offline summary of concepts the bridge depends on, with pointers back to the manifest.

**Vendor LLM** documentation (OpenAI, Anthropic, and similar) is **out of scope** for this folder; optional samples use the **`demo`** extra and upstream provider docs.

## Files

| File | Role |
| ---- | ---- |
| **`README.md`** | This page: pins, refresh rules, licensing choice |
| **`links.manifest.json`** | Version-oriented upstream links for **replayt** and **LangGraph** topics |
| **`bridge-integration-notes.md`** | Offline-friendly concept summary (original wording only) |
