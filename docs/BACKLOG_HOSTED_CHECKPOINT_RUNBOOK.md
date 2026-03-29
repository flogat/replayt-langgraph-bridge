# Backlog spec: Hosted checkpoint runbook — cross-links and integrator checklist

Normative **spec and acceptance criteria** for Mission Control backlog **Hosted checkpoint runbook: tighten cross-links and integrator checklist** (item `af6b342e-289d-4173-a317-2c9815746cbf`). Phase **2** (spec lead) owns this document; phase **3** (builder) implements doc edits against it; phase **2b** (spec gate) checks completeness.

**Goal:** **[HOSTED_DEPLOYMENT_AUTHZ.md](HOSTED_DEPLOYMENT_AUTHZ.md)** and **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** read as **one operator story** for integrators choosing **remote or durable** LangGraph savers. **[README.md](../README.md)** and **[API.md](API.md)** must point integrators to the **same normative anchors** (checklist, non-guarantees, two persistence planes) so no one needs **`src/`** to learn what the bridge **does not** guarantee for **multi-tenant** or **distributed** storage.

**Related normative docs:** threat model **[THREAT_MODEL.md](THREAT_MODEL.md)**; inbound validation **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**; log redaction **[LOG_REDACTION.md](LOG_REDACTION.md)**; checkpoint slice **[BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md](BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md)**.

---

## 1. Canonical anchors (builder must preserve)

These heading texts are **stable contracts** for README / API.md / cross-doc links. If a heading is renamed, **update every inbound link** in the same change set.

| Document | Section | Purpose |
| -------- | ------- | ------- |
| **HOSTED_DEPLOYMENT_AUTHZ.md** | [Integrator runbook: remote checkpoints](HOSTED_DEPLOYMENT_AUTHZ.md#integrator-runbook-remote-checkpoints) | Framing: one story with **CHECKPOINT_PERSISTENCE** |
| **HOSTED_DEPLOYMENT_AUTHZ.md** | [Integrator checklist: remote or multi-tenant checkpoints](HOSTED_DEPLOYMENT_AUTHZ.md#integrator-checklist-remote-or-multi-tenant-checkpoints) | TLS, identity, **`thread_id`** tenancy, secrets |
| **HOSTED_DEPLOYMENT_AUTHZ.md** | [What this package does not guarantee (multi-tenant and distributed storage)](HOSTED_DEPLOYMENT_AUTHZ.md#what-this-package-does-not-guarantee-multi-tenant-and-distributed-storage) | Explicit non-guarantees |
| **CHECKPOINT_PERSISTENCE.md** | [Integrator runbook: remote checkpoints](CHECKPOINT_PERSISTENCE.md#integrator-runbook-remote-checkpoints) | Entry from persistence side; points back to **HOSTED** checklist |
| **CHECKPOINT_PERSISTENCE.md** | [Two persistence planes (LangGraph checkpointer vs replayt Runner / store)](CHECKPOINT_PERSISTENCE.md#two-persistence-planes-langgraph-checkpointer-vs-replayt-runner--store) | Already shipped; README/API must keep linking here |

---

## 2. Content requirements (normative)

### 2.1 One-story narrative

- **HOSTED_DEPLOYMENT_AUTHZ** opening (after title / scope) must state that operators choosing **remote or durable** checkpoints should treat **CHECKPOINT_PERSISTENCE** (what bytes are stored, failure modes, two planes) and **HOSTED_DEPLOYMENT_AUTHZ** (network, identity, tenancy, secrets) as **complementary chapters of one runbook**, not competing docs.
- **CHECKPOINT_PERSISTENCE** must include a short **Integrator runbook: remote checkpoints** section that **mirrors** that intent and links to the **HOSTED** checklist and non-guarantee headings above (no duplicate full checklist required in **CHECKPOINT_PERSISTENCE** beyond a one-line “complete the checklist in **HOSTED**” pointer).

### 2.2 Integrator checklist (minimum topics)

The checklist under **HOSTED_DEPLOYMENT_AUTHZ** (anchored heading in §1) must be **concise** and explicitly cover:

| Topic | Integrator must confirm (summary-level) |
| ----- | ---------------------------------------- |
| **TLS / transport** | Encrypted paths to remote stores and graph APIs where applicable; verified certs; no silent TLS bypass (align with topology **T3** / **T4**). |
| **Identity and authorization** | Who may **invoke** / resume; per-tenant or per-principal credentials; no shared production “god” keys across customers (**T4**). |
| **`thread_id` and tenancy** | **`config["configurable"]["thread_id"]`** (and related namespaces) are **owned by the integrator**; must not collide across tenants; staging vs production separation (**HOSTED** §4 + **CHECKPOINT** resume expectations). |
| **Secret handling** | No secrets or unnecessary PII in **`ReplaytBridgeState["context"]`**; environment / vault-backed credentials; bridge **log redaction** does not protect checkpoint blobs (**CHECKPOINT** §5, **LOG_REDACTION**). |

### 2.3 Non-guarantees (explicit)

**HOSTED_DEPLOYMENT_AUTHZ** must list, in the anchored subsection from §1, that **replayt-langgraph-bridge** does **not** (non-exhaustive but must include these ideas):

- Implement **TLS**, **IAM**, **vault** integration, storage **ACLs**, or **multi-tenant isolation** in application code.
- **Assign**, **validate**, or **scope** LangGraph **`thread_id`** / checkpoint namespaces—only the integrator’s graph **`config`** and deployment layout do.
- **Encrypt or decrypt** checkpoint blobs; **migrate** arbitrary checkpoint bytes across LangGraph versions or tenants.
- Substitute **bridge log redaction** or **inbound state validation** for **checkpoint store access control** or **runtime authentication**.

### 2.4 README and API.md

- **README.md** (**Design principles** security paragraph or **Checkpoint-enabled usage** adjacent text): include **anchored** links to **CHECKPOINT_PERSISTENCE** (two planes + runbook section) and **HOSTED_DEPLOYMENT_AUTHZ** (checklist + non-guarantees), not only bare file paths.
- **API.md** **Cross-spec index**: rows for checkpoint persistence and hosted deployment must use the **same anchors** as README (or strictly equivalent paths) so integrators land on the checklist and non-guarantees without hunting.

---

## 3. Acceptance criteria (testable)

| ID | Criterion | Done when (normative) |
| --- | --------- | ---------------------- |
| **H1** | **One-story framing** | **HOSTED_DEPLOYMENT_AUTHZ** and **CHECKPOINT_PERSISTENCE** each state the paired-doc reading order / runbook intent and cross-link the **Integrator runbook** / checklist anchors. |
| **H2** | **Checklist** | **HOSTED_DEPLOYMENT_AUTHZ** contains the anchored **Integrator checklist** covering **TLS**, **identity/authz**, **`thread_id` tenancy**, and **secret handling** as in §2.2. |
| **H3** | **Non-guarantees** | **HOSTED_DEPLOYMENT_AUTHZ** contains the anchored **What this package does not guarantee** subsection as in §2.3. |
| **H4** | **README** | **README.md** links to **CHECKPOINT_PERSISTENCE** and **HOSTED_DEPLOYMENT_AUTHZ** using the §1 anchors (at least checklist + non-guarantees for **HOSTED**; two planes + runbook entry for **CHECKPOINT**). |
| **H5** | **API.md** | **API.md** cross-spec index links match **H4** anchor targets for the same topics. |
| **H6** | **Traceability** | **HOSTED_DEPLOYMENT_AUTHZ** §7 (or equivalent) and **CHECKPOINT_PERSISTENCE** §8 **Related documents** reference **this backlog file**. |
| **H7** | **Contract tests** | Extend **`tests/test_hosted_deployment_authz_docs.py`** (or add a sibling contract test module) so CI asserts presence of checklist heading, non-guarantee heading, and required keywords (**TLS**, **`thread_id`**, **secret** / **PII**, **does not guarantee** or equivalent). Phase **3** owns test changes; phase **2** specifies the obligation here. |

---

## 4. Non-goals

- **No** new bridge APIs or runtime behavior.
- **No** replacement for upstream LangGraph / replayt security runbooks—only **bridge-scoped** clarity and links.
- **No** duplication of full **THREAT_MODEL** or **STATE_PAYLOAD_VALIDATION** text inside the checklist (link out).

---

## 5. Spec gate / builder checklist (phases 2b / 3)

- [ ] **H1**–**H6** satisfied in the tree; **CHANGELOG.md** **Unreleased** documents integrator-visible doc changes when the Builder lands them.
- [ ] **H7** contract tests green; existing **`test_hosted_deployment_authz_*`** markers (**T1**–**T5**, sample warning, upstream URLs) remain satisfied.
