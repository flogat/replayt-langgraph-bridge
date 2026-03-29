# Hosted deployment: identity, network access, and checkpoint backends

Normative guidance for **deployers** when LangGraph **checkpointers**, **graph runtimes**, or **replayt execution storage** leave a single trusted OS process or cross a network boundary. This document is **factual operational guidance** (TLS, least-privilege storage access, environment separation). It does **not** assert compliance with any regulation or third-party certification.

**Scope:** Integrator-owned configuration—**replayt-langgraph-bridge** does not implement TLS, IAM, vault integration, or storage ACLs. It accepts a LangGraph `Checkpointer` you supply and forwards execution to **replayt** and **LangGraph** as documented in **[API.md](API.md)**.

**Related bridge specs:** checkpoint persistence scope, in-memory vs durable, skew/corruption failure modes, and the **two persistence planes** in **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** (start at **[Integrator runbook: remote checkpoints](CHECKPOINT_PERSISTENCE.md#integrator-runbook-remote-checkpoints)** when coming from this doc); asset and adversary framing in **[THREAT_MODEL.md](THREAT_MODEL.md)**; untrusted inbound dict state in **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**; bridge log redaction (not a substitute for storage access control) in **[LOG_REDACTION.md](LOG_REDACTION.md)**. Spec and acceptance criteria for this runbook shape: **[BACKLOG_HOSTED_CHECKPOINT_RUNBOOK.md](BACKLOG_HOSTED_CHECKPOINT_RUNBOOK.md)**.

---

## Integrator runbook: remote checkpoints

When LangGraph checkpoints become **durable**, **network-attached**, or **shared**, treat **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** and **this document** as **one operator story**:

- **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** is normative for **what** gets serialized into checkpoints, **how** the LangGraph checkpointer plane relates to the replayt **Runner** / **store** plane, and **documented failure modes** (corruption, schema skew, wrong **`thread_id`**).
- **This document** is normative for **controls you must supply**: transport security, **identity**, **`thread_id`** / namespace discipline, and **secrets**—none of which the bridge implements.

You may start from either file; before production, complete both the **persistence contract** and the **checklist** below. The companion entry point on the persistence side: **[CHECKPOINT_PERSISTENCE.md — Integrator runbook: remote checkpoints](CHECKPOINT_PERSISTENCE.md#integrator-runbook-remote-checkpoints)**.

### Integrator checklist: remote or multi-tenant checkpoints

Pre-flight when enabling **remote** or **multi-tenant** checkpoint paths (topologies **T2**–**T5** in [§1](#1-supported-deployment-topologies-and-required-controls)):

- **TLS / transport** — Use **TLS** (or equivalent) to **network-attached** stores and graph APIs; enable **certificate verification**; meet the **T3** / **T4** minimum controls in the topology table.
- **Identity and authorization** — **Authenticate** every **invoke** / resume path that crosses a trust boundary; **authorize** per tenant or principal; do **not** reuse one production “god” credential across customers (**T4**).
- **`thread_id` and tenancy** — Own **`config["configurable"]["thread_id"]`** and backing namespaces (database names, bucket prefixes): **stable per tenant**, **no collisions** across customers, and **separate** dev / stage / prod conventions per [§4](#4-development-staging-and-production). A wrong or reused **`thread_id`** breaks resume isolation—see **[CHECKPOINT_PERSISTENCE.md — §6 Failure modes](CHECKPOINT_PERSISTENCE.md#6-failure-modes-corrupt-data-and-version-skew)**.
- **Secret handling** — Do **not** place secrets or unnecessary **PII** in **`ReplaytBridgeState["context"]`**; serialized checkpoints are **outside** bridge **log redaction** (**[LOG_REDACTION.md](LOG_REDACTION.md)**). Keep credentials in the environment or a secret manager; see **[CHECKPOINT_PERSISTENCE.md — §5 Secrets, PII, and serialized state](CHECKPOINT_PERSISTENCE.md#5-secrets-pii-and-serialized-state)** and **[DESIGN_PRINCIPLES.md — Secrets policy](DESIGN_PRINCIPLES.md#secrets-policy)**.

### What this package does not guarantee (multi-tenant and distributed storage)

**replayt-langgraph-bridge** is a **framework adapter**. Unless a different guarantee is explicitly documented and tested under **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** or **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)**, this package does **not**:

- Implement **TLS**, **network policies**, **IAM** / **RBAC**, **vault** wiring, or storage **ACLs**.
- **Assign**, **validate**, **enforce**, or **scope** **`thread_id`** or checkpoint **namespaces**—your LangGraph **`config`** and deployment do.
- **Encrypt**, **decrypt**, **re-key**, or **migrate** checkpoint **blobs** across LangGraph versions, regions, or tenants.
- Substitute **inbound state validation** (**[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**) or **bridge-originated log redaction** for **checkpoint store access control** or **authenticated remote graph APIs**.

For **which bytes** live in the LangGraph checkpoint plane vs the replayt **Runner** / **store** plane, see **[CHECKPOINT_PERSISTENCE.md — Two persistence planes](CHECKPOINT_PERSISTENCE.md#two-persistence-planes-langgraph-checkpointer-vs-replayt-runner--store)**.

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

---

## 7. Builder-facing acceptance criteria (hosted checkpoint runbook backlog)

Treat Mission Control item **Hosted checkpoint runbook: tighten cross-links and integrator checklist** (`af6b342e-289d-4173-a317-2c9815746cbf`) as **done** when **[BACKLOG_HOSTED_CHECKPOINT_RUNBOOK.md](BACKLOG_HOSTED_CHECKPOINT_RUNBOOK.md)** **§3** (**H1**–**H7**) is satisfied, including contract tests (**H7**) and **CHANGELOG.md** notes for integrator-visible doc edits.
