# Backlog spec: Durable replayt store vs LangGraph checkpoint (single ownership diagram)

Normative **spec and acceptance criteria** for Mission Control backlog **Durable replayt store vs LangGraph checkpoint: single ownership diagram** (item `fae06d2c-c181-4706-b533-f93eb99b8f07`). Phase **2** (spec lead) owns this document; phase **3** (builder) implements against it; phase **2b** (spec gate) checks completeness.

**Related normative docs:** checkpoint slice **[BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md](BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md)** (defers equating the two persistence planes); persistence contract **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)**; inbound validation **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**; hosted backends **[HOSTED_DEPLOYMENT_AUTHZ.md](HOSTED_DEPLOYMENT_AUTHZ.md)**; **README** and **[API.md](API.md)**.

---

## 1. Reconciliation with repository state

**Already documented (must stay true; diagram must not contradict):**

- **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md) §1** — table rows for **LangGraph channel state** (integrator **`Checkpointer`**), **bridge validation wrapper**, and **Replayt `Runner` / store** with separate “owner of format and durability” columns.
- **[BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md](BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md) §2** — explicitly **defers** “equating LangGraph checkpoint durability with replayt **Runner** / **store** durability.”

**Gap (this backlog):** Operators still conflate the two in issues. The builder must add **one** prominent **diagram or table** plus **layered failure-mode bullets** so readers see **two independent durability surfaces** and what each does *not* cover for the other.

---

## 2. User story (normative intent)

As an **operator** or **integrator**, I need **one** visual or tabular explanation that answers:

- **What** LangGraph **`Checkpointer`** persistence stores and who owns its format and lifecycle.
- **What** replayt **`Runner`** + durable store (e.g. **`JSONLStore`**) stores and who owns *that* format and lifecycle.
- **Why** enabling a durable LangGraph checkpoint **does not** replace replayt store configuration (and vice versa).
- **Which** failures happen at **each** layer (not a single “checkpoint” failure bucket).

Readers should **not** need to read **`src/`** to get this mental model.

---

## 3. Acceptance criteria (testable)

### 3.1 Normative home: `docs/CHECKPOINT_PERSISTENCE.md`

Add a **new major section** (recommended placement: **after §1** *Persistence scope: who owns what*, renumber following sections **or** insert as **§1a** / sibling — builder chooses minimal diff, but **§8 Related documents** must stay coherent after renumber).

**Required section heading (stable anchor for links):**

```markdown
## Two persistence planes (LangGraph checkpointer vs replayt Runner / store)
```

Integrators and README will link to **`docs/CHECKPOINT_PERSISTENCE.md#two-persistence-planes-langgraph-checkpointer-vs-replayt-runner--store`** (GitHub-style slug; if the renderer differs, keep the heading text verbatim so anchors stay predictable).

**Required content:**

1. **One diagram or one summary table** (not both mandatory — **at least one** of):
   - **Mermaid** `flowchart` or `block` diagram showing **two parallel stacks** (e.g. left: LangGraph thread / checkpointer / channel state including `ReplaytBridgeState`; right: replayt Runner / JSONL or other store / run records), with a **single** explicit annotation that they are **independent** durability surfaces coordinated by the integrator; **or**
   - **ASCII** art with the same semantics if Mermaid is undesirable for a given doc pipeline.

2. **Short prose** (a few sentences) stating the **non-equivalence** deferred in **[BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md](BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md) §2**: durable graph checkpoints **do not** subsume replayt store durability, and a healthy replayt store **does not** imply LangGraph resume without a compatible checkpointer and `thread_id` story.

3. **Failure modes — bullet lists per layer** (minimum coverage below). Bullets may **summarize** existing §6 (*Failure modes: corrupt data and version skew*) text but must be **grouped by layer** here so operators scan one section:

   | Layer | Minimum failure / risk themes to mention (by name or paraphrase) |
   | ----- | ------------------------------------------------------------------ |
   | **LangGraph checkpointer + serialized graph state** | Blob corruption / deserialization errors owned by LangGraph or saver; **LangGraph** line / format skew across versions; wrong or reused **`thread_id`**; hosted-store network / ACL / TLS issues (pointer to **HOSTED_DEPLOYMENT_AUTHZ** acceptable for detail). |
   | **Bridge inbound validation** (when `checkpointer=` is set) | **`BridgeStateValidationError`** on bad inbound dict-shaped state; **no** new checkpoint from rejected invoke (align with **STATE_PAYLOAD_VALIDATION**). |
   | **Replayt Runner / store (e.g. JSONLStore)** | Store loss or corruption; **workflow definition** change vs old run data; replayt-level errors on resume unrelated to LangGraph checkpoint bytes; integrator responsibility for store path permissions and backup (no bridge guarantee of unified migration). |

4. **Cross-links** in the new section to existing normative sections so the doc does not fork: at minimum **STATE_PAYLOAD_VALIDATION.md**, **HOSTED_DEPLOYMENT_AUTHZ.md** (for hosted checkpoint stores), and **§6** of this file for expanded failure-mode detail.

### 3.2 README (published path, not `src/`)

In the **README** text that discusses **checkpoints** or **checkpoint-enabled** usage (including the **security** blurb that already points at **CHECKPOINT_PERSISTENCE.md**, and/or the **MemorySaver** / resume subsection — builder picks **one** natural insertion point **without** duplicating the whole diagram):

- Add a **single** explicit markdown link to the **new section anchor** in **CHECKPOINT_PERSISTENCE.md** (same heading as §3.1), with anchor text that signals **two persistence planes** / **replayt store vs LangGraph checkpoint** (e.g. “**two persistence planes (replayt store vs LangGraph checkpointer)**”).

**Minimum bar:** A reader skimming README checkpoint guidance discovers the new section **without** opening **`src/`**.

### 3.3 Traceability and related-doc index

- Update **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md)** intro **Backlog traceability** bullet (or adjacent line) to cite this spec **`BACKLOG_DURABLE_REPLAYT_VS_LANGGRAPH_CHECKPOINT.md`** alongside the existing checkpoint-slice pointer.
- Update **[BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md](BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md)** deferred row (§2 table) to link **this** spec as the place where the “do not equate” guidance is expanded for operators.
- Add this file to **[CHECKPOINT_PERSISTENCE.md](CHECKPOINT_PERSISTENCE.md) §8 Related documents** (unless the builder prefers a single “Backlog specs” line — either is fine if discoverable).

### 3.4 Non-goals (hard)

- **No new runtime guarantees** — wording must not imply the bridge synchronizes or merges the two stores, migrates one from the other, or adds a default durable backend. Docs-only unless a **bug** is discovered while editing (then follow normal bugfix / changelog process outside this backlog’s doc scope).
- **No new automated tests** required for this backlog (verification is **spec gate + human** review of rendered docs). Existing checkpoint tests stay as-is unless a doc-driven bugfix forces a small test adjustment.

---

## 4. Changelog policy

When the builder lands **§3.1–§3.3** (integrator-visible **CHECKPOINT_PERSISTENCE** section + **README** link), add **`CHANGELOG.md` — Unreleased** documentation bullet per **CONTRIBUTING.md** / **RELEASE_CHANGELOG.md**.

**Phase 2 (this spec file only):** A **Documentation** changelog entry for the **backlog spec** itself is optional; if maintainers already log phase-2 specs (see prior **PEP 561** / **gitignore** entries), one line may reference this file.

---

## 5. Spec gate / builder checklist (phases 2b / 3)

- [x] **CHECKPOINT_PERSISTENCE.md** contains **§ Two persistence planes (LangGraph checkpointer vs replayt Runner / store)** with diagram **or** table per §3.1.
- [x] Same section includes **layer-grouped failure-mode bullets** covering the three rows in §3.1 table (checkpointer, bridge validation, replayt store).
- [x] **README** links to that section with operator-meaningful anchor text per §3.2.
- [x] **BACKLOG_LANGGRAPH_CHECKPOINT_SLICE.md** deferred cross-link updated; **CHECKPOINT_PERSISTENCE.md** traceability + §8 (or equivalent) updated per §3.3.
- [x] **CHANGELOG.md — Unreleased** updated when user-facing doc ships (§4).
