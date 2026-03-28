# Hosted deployment: identity, network access, and checkpoint backends

Normative guidance for **deployers** when LangGraph **checkpointers**, **graph runtimes**, or **replayt execution storage** leave a single trusted OS process or cross a network boundary. This document is **factual operational guidance** (TLS, least-privilege storage access, environment separation). It does **not** assert compliance with any regulation or third-party certification.

**Scope:** Integrator-owned configuration—**replayt-langgraph-bridge** does not implement TLS, IAM, vault integration, or storage ACLs. It accepts a LangGraph `Checkpointer` you supply and forwards execution to **replayt** and **LangGraph** as documented in **[API.md](API.md)**.

**Related bridge specs:** checkpoint persistence scope, in-memory vs durable, and skew/corruption failure modes in **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)**; asset and adversary framing in **[THREAT_MODEL.md](THREAT_MODEL.md)**; untrusted inbound dict state in **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**; bridge log redaction (not a substitute for storage access control) in **[LOG_REDACTION.md](LOG_REDACTION.md)**.

---

## 1. Supported deployment topologies and required controls

The table below lists **documented** patterns for using the bridge with durable or remote components. “Supported” here means **we describe the controls integrators should apply**—not that the bridge ships a specific backend.

| ID | Topology | Summary | Required controls (minimum) |
| --- | --- | --- | --- |
| **T1** | In-process graph, **no** durable LangGraph checkpoint | `compile_replayt_workflow` with `checkpointer=None` (bridge default) or only ephemeral in-memory use | Host and process identity are the trust boundary: restrict shell access, avoid shared interactive users for production. **Replayt** `Runner` / store placement follows **replayt**’s own deployment expectations (see [Upstream: replayt](#3-upstream-replayt)). |
| **T2** | Single-host **durable** checkpoint (e.g. SQLite file, local disk) | LangGraph checkpointer writes to paths on one machine | Filesystem **ACLs** and dedicated OS user for the service; **encryption at rest** and backup policy per organization; **no** shared writable directory across untrusted tenants without stronger isolation (separate DB files, bind mounts, or VMs). |
| **T3** | **Network-attached** checkpoint store (managed SQL, object store, etc.) | Checkpointer uses a remote database or bucket | **TLS** (or equivalent) on the wire with **certificate verification**; **unique credentials per environment**; database **roles** / IAM policies with **least privilege** (narrow table/bucket prefix, no admin unless required); **network policies** so only approved workloads reach the store; **audit logs** where the platform provides them. |
| **T4** | **Remote** LangGraph runtime or HTTP-exposed graph API | Execution or checkpoint API outside the application process | **Authenticate** every invoke/resume path; **authorize** per tenant/thread (no shared “god” API key across customers); **mTLS or signed requests** where feasible; rate limits and separate **dev / stage / prod** endpoints and credentials. |
| **T5** | **Shared** replayt-oriented persistence (runner store, approvals) | Multiple services or operators share replayt backing storage | **Tenant or namespace separation** in configuration; access control on the store consistent with replayt’s model; document who may **read vs write** resume/approval state. |

If a topology mixes **T3** and **T4**, apply the **union** of controls (networked storage **and** remote API rules).

---

## 2. IAM-style patterns (integrator responsibility)

These are **patterns**, not vendor-specific runbooks:

- Prefer **short-lived credentials** (rotation, workload identity) over long-lived static passwords embedded in graph state.
- Use **separate principals** (service accounts, DB users, bucket policies) for **development**, **staging**, and **production**.
- For object storage: **deny public** read/write; scope policies to known prefixes or tables; avoid wildcard principals for **write** access.
- For SQL: application role should not hold **superuser** or **DDL** rights unless required; use connection limits where available.

---

## 3. Upstream references

### LangGraph

- **Persistence and checkpoints (official docs):** [LangGraph persistence — Python](https://docs.langchain.com/oss/python/langgraph/persistence)
- **Security advisories and reports:** [langgraph `Security` on GitHub](https://github.com/langchain-ai/langgraph/security)

LangGraph maintainers have published guidance on **hardening checkpoint deserialization** (for example environment variables such as `LANGGRAPH_STRICT_MSGPACK` and configuration of allowed deserialization modules). Integrators using remote or shared checkpoint stores should read the current upstream **security** and **persistence** documentation for the **langgraph** version they run—this bridge does not duplicate those instructions. Example published advisory (historical context; always follow the version you run): [GHSA-g48c-2wqr-h844](https://github.com/langchain-ai/langgraph/security/advisories/GHSA-g48c-2wqr-h844).

### replayt

- **Package index and published metadata:** [replayt on PyPI](https://pypi.org/project/replayt/)

The **replayt** distribution’s security notes, changelog, and project links appear on **PyPI** and in materials published by the **replayt** maintainers. This bridge **consumes** replayt’s public API; **workflow definition**, **handlers**, **Runner**, and **store** security remain **integrator- and replayt-documented** concerns. If **replayt** adds a dedicated security page, link it from this section in the same commit that updates the URL.

---

## 4. Development, staging, and production

- Use **separate** checkpoint **namespaces** (e.g. distinct `thread_id` conventions, database names, or bucket prefixes) so a staging client cannot resume or overwrite production threads by mistake.
- Do **not** point production graphs at development databases or shared demo buckets.
- Align secret rotation so **staging** and **production** credentials do not overlap in a way that allows cross-environment access.

---

## 5. Samples and permissive defaults (required warning)

> **Warning — samples are not production security baselines.** Repository examples (including the README **Usage** snippet) often omit a `Checkpointer` or use **convenience** patterns (for example `.env` files in **Secrets handling**) to keep copy-paste short. That does **not** imply:
>
> - safe defaults for **multi-tenant** deployments,
> - **encryption at rest** or **TLS** to remote stores,
> - or **least-privilege** IAM for checkpoint or graph APIs.

**In-memory** LangGraph checkpoint implementations are appropriate for **unit tests and local debugging**, not for **durable** multi-tenant state. Before production, map your layout to **[§1 Supported deployment topologies](#1-supported-deployment-topologies-and-required-controls)** and implement the listed controls.

---

## 6. Builder-facing acceptance criteria (documentation backlog)

Treat the following as **done** when this backlog item is fully delivered in the tree:

- [x] **`docs/` topology section** — Table **T1–T5** with required controls per row (this document).
- [x] **Explicit sample warning** — [§5](#5-samples-and-permissive-defaults-required-warning) plus README **Usage** callout (see README).
- [x] **Upstream cross-links** — LangGraph persistence and GitHub Security; replayt PyPI (and placeholder note for future replayt security URL).

Future **code or sample** changes that introduce checkpointing or remote services should **repeat** a short warning in-repo if they use **permissive** defaults for brevity.
