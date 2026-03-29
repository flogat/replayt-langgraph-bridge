# Backlog spec: First-party opt-in LLM sample under `examples/` (`demo` extra)

Normative **spec and acceptance criteria** for Mission Control backlog **Ship first-party opt-in LLM sample under examples/ with demo extra** (item `74a40ce9-cd64-4ab3-bda8-50296e094201`). Phase **2** (spec lead) owns this document; phase **3** (builder) implements against it; phase **2b** (spec gate) checks completeness.

**Related normative docs:** **[MISSION.md](MISSION.md#llm-demos-and-optional-samples-scope)**; **[DESIGN_PRINCIPLES.md — LLM and demos](DESIGN_PRINCIPLES.md#llm-and-demos)** (S1–S4); **[LOG_REDACTION.md](LOG_REDACTION.md)**; **[DESIGN_PRINCIPLES.md — Secrets policy](DESIGN_PRINCIPLES.md#secrets-policy)**; **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** §3.4; **[Core vs demo extras](DESIGN_PRINCIPLES.md#core-vs-demo-extras-llm-clients-and-supply-chain)**; root **`pyproject.toml`** optional **`demo`** group.

---

## 1. Reconciliation with repository state

**Already satisfied (must remain true after implementation):**

- Optional **`[demo]`** extra lists **openai**, **anthropic**, **langchain-openai**, and **langchain-anthropic** under **`[project.optional-dependencies]`** with README extras matrix coverage.
- Primary GitHub Actions job **`test`** uses **`uv sync --frozen --extra dev`** (no **`demo`**), full **pytest** collection, **ruff**, **mypy** — **no** scripted live vendor LLM calls.
- **`tests/test_dependency_strategy.py`** (or successor) enforces demo-only packages stay out of core deps.

**Gap (this backlog):** There is **no** committed **runnable** first-party script under **`examples/`** that exercises the bridge together with a **live** (or live-capable) LangChain chat model behind **`[demo]`** installs. Integrators lack a **minimal, copy-paste** pattern that stays aligned with **MISSION** / **DESIGN_PRINCIPLES** posture.

---

## 2. User story (normative intent)

As an **integrator**, I can:

1. Install **`replayt-langgraph-bridge[demo]`** and run a **single** documented Python file under **`examples/`** (default filename **`examples/llm_node_graph.py`**) that compiles a **replayt** **`Workflow`** through **`compile_replayt_workflow`** and performs at least **one** graph step that calls a **vendor LLM** via the **LangChain** bindings shipped in the **`demo`** extra.
2. Read **README**, the **example file header / module docstring**, and this spec to learn **which environment variables** to set, that **usage is vendor-metered**, and how **logging** must stay consistent with **Secrets policy** and **[LOG_REDACTION.md](LOG_REDACTION.md)** for bridge-originated logs.

As a **maintainer**, I keep **default CI** unchanged: **`[dev]`**-only frozen install, **no** **`demo`** in the **`test`** job, **no** pytest module that **requires** demo imports without **`importorskip`** / skip (per **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** §3.4).

---

## 3. Acceptance criteria (testable)

### 3.1 Example artifact

| Criterion | Done when (normative) |
| --------- | ---------------------- |
| **Path and runnability** | Repo root contains **`examples/llm_node_graph.py`** (or a **single** renamed file under **`examples/`** if the Builder documents the rename **in README, this spec §8, and the spec gate checklist** — default remains **`llm_node_graph.py`**). The script is executable as **`python examples/<name>.py`** from a clone after installing **`[demo]`** (document **`uv`** / **`pip`** incantations in README). |
| **Bridge usage** | Uses **supported** public bridge APIs (at minimum **`compile_replayt_workflow`** and **`initial_bridge_state`** or equivalent documented pattern) with a **replayt** **`Workflow`** whose steps include **at least one** LLM call routed through **LangChain** (**`langchain-openai`** and/or **`langchain-anthropic`** — at least **one** provider path must work when the integrator sets the right env vars; optional dual-provider switch via env is allowed if documented). |
| **`__main__`** | Entry point guarded by **`if __name__ == "__main__":`**; missing required credentials fail fast with a **clear** message naming the **environment variable(s)** (no silent no-op). |

### 3.2 Packaging and dependencies

| Criterion | Done when (normative) |
| --------- | ---------------------- |
| **`demo` only for LLM clients** | The example imports **only** LLM vendor / LangChain client modules that are already declared under **`[project.optional-dependencies] demo`** (or adds **no** new direct imports; if a **new** demo-only package is justified, it lands **only** under **`demo`** with **`pyproject.toml`** comment, README matrix update, and **contract test** update per **[Core vs demo extras](DESIGN_PRINCIPLES.md#core-vs-demo-extras-llm-clients-and-supply-chain)**). |
| **Not part of default package imports** | The file lives under **`examples/`**, **not** under **`src/replayt_langgraph_bridge/`**; **`pip install replayt-langgraph-bridge`** (no extras) must **not** require the example to import. |
| **Lockfile / CI** | Root **`uv.lock`** continues to reflect the **CI-relevant** **`[dev]`** graph (**no** requirement to fold **`demo`** into **`uv.lock`** for default **`test`**). The **`test`** job **must not** add **`--extra demo`** or equivalent. Integrators opt in with an explicit **`[demo]`** install when running the sample. |

### 3.3 Environment variables, cost, and LangChain-operational vars

| Criterion | Done when (normative) |
| --------- | ---------------------- |
| **Provider keys** | README **LLM demos** section **and** the example’s top-level docstring list **`OPENAI_API_KEY`** and **`ANTHROPIC_API_KEY`** as applicable to whichever provider path(s) the script supports (if only one provider is implemented, state which key is **required** vs **unused**). |
| **LangChain / tracing** | If the sample sets tracing, custom endpoints, or LangSmith-related behavior, document **additional** env vars actually read by the code path (e.g. **`LANGCHAIN_API_KEY`**, **`LANGCHAIN_TRACING_V2`**, **`LANGCHAIN_PROJECT`**) with a pointer to **upstream** LangChain docs for drift; if unused, state **“not used by this sample”** explicitly. |
| **`.env.example`** | If new **name-only** variables are introduced beyond those already commented in **`.env.example`**, extend **`.env.example`** with **`#`** comment lines only (no values), per **[Secrets policy](DESIGN_PRINCIPLES.md#secrets-policy)**. |
| **Cost** | README and example docstring state that calls are **vendor-metered**, may incur **charges**, and that this package **does not** enforce quotas or billing limits. |

### 3.4 Logging, redaction, and secrets

| Criterion | Done when (normative) |
| --------- | ---------------------- |
| **No secrets in repo** | No **`.env`**, keys, tokens, or prompt dumps committed; sample does not **print** or **log** raw API keys or full prompts/completions unless explicitly justified and called out as **out of bridge redaction scope** (default: **do not**). |
| **Bridge logs** | If the sample triggers **bridge-originated** structured logging, behavior remains consistent with **[LOG_REDACTION.md](LOG_REDACTION.md)**; docstring or README points integrators at that doc. |
| **Application logging** | Sample code avoids **stdlib** **`logging`** / **print** patterns that would leak credentials or sensitive user content; prefer minimal, non-sensitive status messages. |

### 3.5 README and normative docs refresh

| Criterion | Done when (normative) |
| --------- | ---------------------- |
| **README** | **LLM demos** section links to **`examples/llm_node_graph.py`** (or chosen name), shows **`pip install` / `uv sync`** with **`[demo]`**, repeats **CI** boundary (**`[dev]`**-only **`test`** job, **no** live LLM in default CI), and covers env vars + cost + redaction pointers (may briefly summarize; **DESIGN_PRINCIPLES** / **LOG_REDACTION** remain authoritative). |
| **MISSION.md** | **[LLM demos and optional samples](MISSION.md#llm-demos-and-optional-samples-scope)** updated: **shipped** first-party sample is **yes** with path to **`examples/`** and same opt-in / CI constraints. |
| **DESIGN_PRINCIPLES.md** | **Current repository state** table under **[LLM and demos](DESIGN_PRINCIPLES.md#llm-and-demos)** updated to match (**runnable** sample **shipped**; pointer to **`examples/`**). **S2** in the product table applies; **S3** “not included” text moves to historical note or is removed where it would contradict reality. |

### 3.6 Automated tests and CI

| Criterion | Done when (normative) |
| --------- | ---------------------- |
| **Default pytest** | **`uv sync --frozen --extra dev`** + **`uv run pytest`** (no path filter) stays **green** without **`demo`** installed. |
| **No accidental collection** | No test module **imports** **`examples/*.py`** in a way that runs LLM code at import time. Any future test that imports **`demo`**-only modules uses **`pytest.importorskip`** / **`skip`** with reason naming **`[demo]`** per **[REPLAYT_BOUNDARY_TESTS.md](REPLAYT_BOUNDARY_TESTS.md)** §3.4. |
| **No CI demo install** | **`.github/workflows/ci.yml`** **`test`** job does **not** install **`demo`** and does **not** add steps that call live models. |

### 3.7 Changelog

| Criterion | Done when (normative) |
| --------- | ---------------------- |
| **Unreleased** | **`CHANGELOG.md`** gains an **Unreleased** bullet when the Builder lands the sample and doc updates (integrator-visible **Added** / **Documentation** entry per **[CONTRIBUTING.md](CONTRIBUTING.md)**). **No** **Unreleased** entry is required for **this phase-2 spec file alone**. |

---

## 4. Non-goals (hard)

- **Not** adding **live** LLM calls to **default CI** or to **`[dev]`**-only pytest runs.
- **Not** expanding **`demo`** into **`uv.lock`** / **`test`** job unless a **separate** backlog explicitly changes dependency-lock policy for optional extras.
- **Not** a production-ready **hosted** deployment, checkpoint hardening, or **THREAT_MODEL** expansion beyond what existing docs already require.
- **Not** multiple large tutorials; **one** minimal **runnable** example satisfies the backlog unless maintainers explicitly split work in a follow-up issue.

---

## 5. Open choices (builder resolves; document in PR)

| Topic | Guidance |
| ----- | -------- |
| **Single vs dual provider** | Minimum **one** working provider; second is optional if env vars and behavior are documented. |
| **Checkpointing** | In-memory / no checkpointer is acceptable for minimalism; durable checkpoint patterns stay in **README** / **CHECKPOINT_PERSISTENCE.md** unless the sample’s purpose is clearer with **`MemorySaver`**. |
| **LLM step shape** | Prefer a **single** replayt step that calls LangChain chat model; avoid unnecessary graph complexity. |

---

## 6. Spec gate / builder checklist (phases 2b / 3)

- [ ] **`examples/llm_node_graph.py`** (or documented alternate under **`examples/`**) implements §3.1–§3.2.
- [ ] §3.3 env / cost / LangChain vars documented in README + example + **`.env.example`** delta if needed.
- [ ] §3.4 logging / redaction / secrets posture satisfied.
- [ ] §3.5 **README**, **MISSION.md**, **DESIGN_PRINCIPLES.md** updated; **S2** satisfied.
- [ ] §3.6 CI and pytest default path unchanged and green.
- [ ] §3.7 **CHANGELOG.md — Unreleased** updated.
- [ ] **`tests/test_dependency_strategy.py`** (or equivalent) still matches **`pyproject.toml`** if **`demo`** deps change.

---

## 7. Tester / phase 4 hints

- Verify **`pytest`** on **`[dev]`**-only install with **no** network credentials in CI env.
- Manual smoke (document in PR or maintainer notes): **`pip install -e ".[demo]"`** (or **`uv sync --extra demo`**), set **one** provider key, run **`python examples/llm_node_graph.py`**, confirm **one** successful completion.
- grep guard (optional): ensure **`examples/`** does not contain string patterns resembling committed secrets (follow **[GITIGNORE_AND_LOCAL_ARTIFACTS.md](GITIGNORE_AND_LOCAL_ARTIFACTS.md)**).

---

## 8. Document history

| Phase | Action |
| ----- | ------ |
| **2** (spec lead) | Added this backlog spec; default example filename **`examples/llm_node_graph.py`**. |
| **3** (builder) | Implement §3; if filename differs, update §8 and all inbound links. |
