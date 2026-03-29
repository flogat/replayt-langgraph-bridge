# replayt-langgraph-bridge

LangGraph adapter mapping replayt workflow states to graph nodes and checkpoints.

This project builds on **replayt** as a **LangGraph framework bridge**. Read
**[docs/REPLAYT_ECOSYSTEM_IDEA.md](docs/REPLAYT_ECOSYSTEM_IDEA.md)** for the primary pattern and compatibility stance, then
**[docs/MISSION.md](docs/MISSION.md)** for users, scope, success metrics, and version intent.

## Design principles

**[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** covers **replayt** compatibility, versioning, integrator security
expectations, and optional **LLM** demo boundaries.

For a detailed threat model on checkpoint and state data, see **[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)**. To report a **security vulnerability privately**, see **[SECURITY.md](SECURITY.md)**. For **what is persisted, in-memory vs durable checkpointers, failure modes for bad or version-skewed data**, and **builder test obligations** for checkpoint paths without live credentials, see **[docs/CHECKPOINT_PERSISTENCE.md](docs/CHECKPOINT_PERSISTENCE.md)** — including **[Integrator runbook: remote checkpoints](docs/CHECKPOINT_PERSISTENCE.md#integrator-runbook-remote-checkpoints)** and **[Two persistence planes (LangGraph checkpointer vs replayt Runner / store)](docs/CHECKPOINT_PERSISTENCE.md#two-persistence-planes-langgraph-checkpointer-vs-replayt-runner--store)**. For **hosted LangGraph or remote checkpoint backends** (topologies, TLS, access control, environment separation, upstream links), see **[docs/HOSTED_DEPLOYMENT_AUTHZ.md](docs/HOSTED_DEPLOYMENT_AUTHZ.md)** — including **[Integrator checklist: remote or multi-tenant checkpoints](docs/HOSTED_DEPLOYMENT_AUTHZ.md#integrator-checklist-remote-or-multi-tenant-checkpoints)** and **[what this package does not guarantee (multi-tenant and distributed storage)](docs/HOSTED_DEPLOYMENT_AUTHZ.md#what-this-package-does-not-guarantee-multi-tenant-and-distributed-storage)**. For the **log redaction** contract (defaults, strict mode, integrator hook) for bridge-originated structured logs, see **[docs/LOG_REDACTION.md](docs/LOG_REDACTION.md)**. For **inbound bridge state** validation (enforced limits, schema version, checkpoint safety), see **[docs/STATE_PAYLOAD_VALIDATION.md](docs/STATE_PAYLOAD_VALIDATION.md)**. For **replayt boundary** tests and actionable failure messages, see **[docs/REPLAYT_BOUNDARY_TESTS.md](docs/REPLAYT_BOUNDARY_TESTS.md)**. For the **stable public export set**, module layout, and stability rules, see **[docs/API.md](docs/API.md)**. For **LangGraph `stream` / `astream` / `ainvoke` vs the CI-tested synchronous `invoke` path**, see **[docs/API.md — Streaming and async entry points](docs/API.md#streaming-and-async-langgraph-entry-points-invoke-stream-astream)**.

## Dependency strategy

This project follows a deliberate **dependency and pin policy** so downstream installs do not pick up unexpected **major** upgrades of **replayt** or **LangGraph**.

- **Runtime** (installed with `pip install replayt-langgraph-bridge`): `replayt>=0.4.0,<0.5` and `langgraph>=1.1.0,<1.2`, declared in **`pyproject.toml`** with short comments explaining bounds.
- **Minimum supported** vs **upper bounds**: Lower bounds reflect features and support posture; `< next-major` caps automatic upgrades until maintainers validate a new line.
- **What CI exercises**: **Python** 3.11, **3.12**, and **3.13** jobs install **`[dev]`** from committed **`uv.lock`** (**`uv sync --frozen --extra dev`**) and run **`uv run pytest`** (no path or marker filter), **`uv run ruff check src tests`**, and **`uv run mypy -p replayt_langgraph_bridge`**—**without** any optional **`demo`** extra. The **pytest** run collects **unit tests and contract-style replayt boundary tests** together; normative scope and acceptance mapping are in **[docs/REPLAYT_BOUNDARY_TESTS.md](docs/REPLAYT_BOUNDARY_TESTS.md)**. That proves the integrator-relevant install path stays green when demo-only LLM client dependencies are not present. Regeneration and security→lock workflow: **[docs/DEPENDENCY_LOCK_STRATEGY.md](docs/DEPENDENCY_LOCK_STRATEGY.md)**.
- **Contributor install (locked, matches CI):** **`uv sync --frozen --extra dev`** (see **[CONTRIBUTING.md](CONTRIBUTING.md)**). **`pip install -e ".[dev]"`** still resolves loosely for ad-hoc work but is not the CI graph.
- **Upstream majors or risky bumps**: Use the **Compatibility Update** issue template (`.github/ISSUE_TEMPLATE/compatibility_update.md`) and follow the maintainer checklist in **[docs/DESIGN_PRINCIPLES.md#dependency-and-pin-policy](docs/DESIGN_PRINCIPLES.md#dependency-and-pin-policy)**.

The full policy (selection rules, LangGraph major rollout risk, **core vs demo LLM extras**, and builder-facing acceptance criteria) lives in **[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)**.

### Optional extras matrix

| Install command | Purpose | Declared outbound LLM vendor clients |
| --- | --- | --- |
| `pip install replayt-langgraph-bridge` | Core bridge runtime (**replayt**, **langgraph** per `pyproject.toml`) | **No** — core must not list LLM provider SDKs; see **[DESIGN_PRINCIPLES.md — Core vs demo extras](docs/DESIGN_PRINCIPLES.md#core-vs-demo-extras-llm-clients-and-supply-chain)** |
| `pip install replayt-langgraph-bridge[dev]` | Contributor tooling (**pytest**, **ruff**, **pip-audit**, **mypy** smoke) | **No** |
| `pip install replayt-langgraph-bridge[demo]` | Optional **openai**, **anthropic**, **langchain-openai**, and **langchain-anthropic** for samples that call vendor LLM APIs (see `pyproject.toml`) | **Yes** |

**Note:** **langgraph** (and its transitive dependencies) may include generic HTTP or messaging libraries used by the framework; the matrix above refers to **direct** bridge requirements that exist primarily to invoke **LLM vendor** APIs. Transitive behavior follows upstream packages you install.

### LLM demos (optional samples)

**Shipped sample:** **[`examples/llm_node_graph.py`](examples/llm_node_graph.py)** is a minimal replayt + LangGraph example with one LangChain-backed LLM step. It is **not** imported by the default package; run it only after installing **`[demo]`**. Normative acceptance detail lives in **[docs/BACKLOG_FIRST_PARTY_LLM_SAMPLE.md](docs/BACKLOG_FIRST_PARTY_LLM_SAMPLE.md)**. Scope and policy are normative in **[docs/MISSION.md](docs/MISSION.md#llm-demos-and-optional-samples-scope)** and **[docs/DESIGN_PRINCIPLES.md — LLM and demos](docs/DESIGN_PRINCIPLES.md#llm-and-demos)**.

**Install and run (local, opt-in):**

```bash
pip install -e ".[demo]"
# or: uv sync --extra demo
export OPENAI_API_KEY=...   # and/or ANTHROPIC_API_KEY; optional LLM_PROVIDER=openai|anthropic
python examples/llm_node_graph.py
```

**Environment variables:** The example and **[`.env.example`](.env.example)** describe **`OPENAI_API_KEY`**, **`ANTHROPIC_API_KEY`**, and optional **`LLM_PROVIDER`**. The sample does **not** enable LangSmith / LangChain tracing env vars; see upstream LangChain docs if you add tracing. Do not commit **`.env`** or raw keys. See **[Secrets handling](#secrets-handling)** and **[docs/DESIGN_PRINCIPLES.md#secrets-policy](docs/DESIGN_PRINCIPLES.md#secrets-policy)**.

**Cost:** Usage is **metered and billed by the model vendor** (and any tracing SaaS you enable). This package does not cap spend or hide charges.

**Logs and redaction:** Bridge-originated structured logs follow **[docs/LOG_REDACTION.md](docs/LOG_REDACTION.md)**. The sample avoids printing keys or model text; treat graph context like any persistence boundary if you extend it.

**CI:** The default **`test`** job syncs **`[dev]`** only from **`uv.lock`**, runs **`uv run pytest`**, **ruff**, and the **mypy** package smoke, with **no** **`[demo]`** install and **no** live LLM calls (**[`.github/workflows/ci.yml`](.github/workflows/ci.yml)**).

## Reference documentation (optional)

This checkout does not yet include [`docs/reference-documentation/`](docs/reference-documentation/). You can add markdown
copies of upstream replayt documentation there for offline review or agent context.

## Installation

```bash
pip install replayt-langgraph-bridge
```

### Secrets handling
**Important**: Never commit secrets to version control. Store API keys and tokens in environment variables. For a **tracked**, comment-only list of common variable names, see **[`.env.example`](.env.example)** (copy to **`.env`** locally; **`.env`** is gitignored).

**Note:** The `.env` examples below are **developer convenience** only. Production should use a secret manager and the network and access controls in **[docs/HOSTED_DEPLOYMENT_AUTHZ.md](docs/HOSTED_DEPLOYMENT_AUTHZ.md)**.

**Example setup**:
```bash
# Set environment variables (Linux/macOS)
export OPENAI_API_KEY="your-key-here"
export LANGCHAIN_API_KEY="your-key-here"

# Or use a .env file (but never commit it!)
echo "OPENAI_API_KEY=your-key-here" >> .env
echo "LANGCHAIN_API_KEY=your-key-here" >> .env
```

**In code**:
```python
import os

# Read secrets from environment (keep imports limited to what you use;
# bridge usage examples are in **Usage** below).
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# Use the key in your workflow
# ... (your workflow code here)
```

For the complete secrets policy, see **[docs/DESIGN_PRINCIPLES.md#secrets-policy](docs/DESIGN_PRINCIPLES.md#secrets-policy)**. Contributor-focused **`.gitignore`** rules and a “must never commit” checklist live in **[docs/GITIGNORE_AND_LOCAL_ARTIFACTS.md](docs/GITIGNORE_AND_LOCAL_ARTIFACTS.md)** and **[CONTRIBUTING.md](CONTRIBUTING.md#what-must-never-be-committed)**.

## Usage

**Warning:** This snippet uses **no** LangGraph `Checkpointer` and is only a minimal API example—not a production topology (no durable checkpoint isolation, TLS, or IAM). See **[docs/HOSTED_DEPLOYMENT_AUTHZ.md](docs/HOSTED_DEPLOYMENT_AUTHZ.md)** before exposing graphs or checkpoints beyond a trusted local process.

```python
from replayt.workflow import Workflow
from replayt_langgraph_bridge import compile_replayt_workflow, initial_bridge_state

# Define a replayt workflow
wf = Workflow()

@wf.step("start")
def start(ctx):
    print("Starting workflow")
    return "next_step"

@wf.step("next_step")
def next_step(ctx):
    print("Next step")
    return "end"

# Compile the workflow into a LangGraph runnable
graph = compile_replayt_workflow(wf)

# Create initial state
initial_state = initial_bridge_state()

# Run the graph (example, requires LangGraph runtime)
# result = graph.invoke(initial_state)
```

### Checkpoint-enabled usage (LangGraph 1.1.x)

**Ephemeral, in-process only:** `MemorySaver` fits tests and local debugging; state is lost when the process exits and this is not a production topology. For durable or hosted stores, follow the paired runbook: **[Integrator runbook: remote checkpoints](docs/CHECKPOINT_PERSISTENCE.md#integrator-runbook-remote-checkpoints)** and **[Two persistence planes](docs/CHECKPOINT_PERSISTENCE.md#two-persistence-planes-langgraph-checkpointer-vs-replayt-runner--store)** in **[docs/CHECKPOINT_PERSISTENCE.md](docs/CHECKPOINT_PERSISTENCE.md)**, plus **[Integrator checklist: remote or multi-tenant checkpoints](docs/HOSTED_DEPLOYMENT_AUTHZ.md#integrator-checklist-remote-or-multi-tenant-checkpoints)** and **[non-guarantees for multi-tenant / distributed storage](docs/HOSTED_DEPLOYMENT_AUTHZ.md#what-this-package-does-not-guarantee-multi-tenant-and-distributed-storage)** in **[docs/HOSTED_DEPLOYMENT_AUTHZ.md](docs/HOSTED_DEPLOYMENT_AUTHZ.md)**. The **`invoke`** / **`config`** shape matches **`tests/test_bridge_graph.py`**.

```python
from uuid import uuid4

from langgraph.checkpoint.memory import MemorySaver
from replayt.persistence import JSONLStore
from replayt.runner import Runner
from replayt.workflow import Workflow

from replayt_langgraph_bridge import compile_replayt_workflow, initial_bridge_state

wf = Workflow("checkpoint_demo")

@wf.step("start")
def start(ctx):
    ctx.set("visit", 1)
    return "next_step"

@wf.step("next_step")
def next_step(ctx):
    ctx.set("visit", ctx.get("visit", 0) + 1)
    return None

wf.set_initial("start")
wf.note_transition("start", "next_step")

store = JSONLStore("events.jsonl")  # use a temp path in real tests
runner = Runner(wf, store)
runner.run_id = str(uuid4())

graph = compile_replayt_workflow(wf, checkpointer=MemorySaver())
config = {"configurable": {"thread_id": "example-thread"}}

result = graph.invoke(
    initial_bridge_state(),
    config=config,
    context={"runner": runner},
)
# result["context"]["visit"] == 2 after both steps complete
```

### Human-in-the-loop (`interrupt_before` / `interrupt_after`)

**`interrupt_*`** lists use **replayt** step names (the same strings as **`@workflow.step(...)`** and **`note_transition`**); they are forwarded to LangGraph **`StateGraph.compile`**. See **[docs/API.md](docs/API.md)** (`compile_replayt_workflow`). Ordering when you pass both lists follows upstream **`compile`** (this bridge does not reorder them).

Copy-paste pattern: **`MemorySaver`**, stable **`thread_id`** in **`config["configurable"]`**, **`Runner`** + store with **`run_id`** set, **`context={"runner": runner}`** on **every** **`invoke`** for that thread, then **`invoke(None, ...)`** to resume. Persistence and resume expectations: **[docs/CHECKPOINT_PERSISTENCE.md](docs/CHECKPOINT_PERSISTENCE.md)** §7. Regression tests: **`tests/test_bridge_graph.py`** — **`test_resume_second_invoke_uses_memory_checkpointer`** (**`interrupt_before`**), **`test_resume_second_invoke_interrupt_after_first_uses_memory_checkpointer`** (**`interrupt_after`**). Disk **`SqliteSaver`** resume after a fresh **`compile_replayt_workflow`**: **`tests/test_disk_checkpoint_sqlite_roundtrip.py`** (CI and **`uv sync --frozen --extra dev`** pull in **`langgraph-checkpoint-sqlite`** via **`[dev]`** / **`uv.lock`**; **`pytest`** skips that module when the namespace is missing, e.g. editable core-only **`pip install -e .`**).

```python
from uuid import uuid4

from langgraph.checkpoint.memory import MemorySaver
from replayt.persistence import JSONLStore
from replayt.runner import Runner
from replayt.workflow import Workflow

from replayt_langgraph_bridge import compile_replayt_workflow, initial_bridge_state

wf = Workflow("hitl_demo")

@wf.step("first")
def first(ctx):
    ctx.set("phase", 1)
    return "second"

@wf.step("second")
def second(ctx):
    ctx.set("phase", ctx.get("phase", 0) + 10)
    return None

wf.set_initial("first")
wf.note_transition("first", "second")

store = JSONLStore("hitl_events.jsonl")  # use a temp path in real tests
runner = Runner(wf, store)
runner.run_id = str(uuid4())

saver = MemorySaver()
graph = compile_replayt_workflow(
    wf,
    checkpointer=saver,
    interrupt_after=["first"],  # pause after the first step (replayt name)
)
config = {"configurable": {"thread_id": "hitl-thread"}}

out1 = graph.invoke(
    initial_bridge_state(context={"seed": True}),
    config=config,
    context={"runner": runner},
)
# LangGraph 1.1.x: first step ran; bridge leaves replayt_next at the next step name.
assert out1["context"]["phase"] == 1
assert out1["replayt_next"] == "second"

out2 = graph.invoke(None, config=config, context={"runner": runner})
assert out2["context"]["phase"] == 11
assert out2["replayt_next"] == ""
```

To **pause and resume** across two **`invoke`** calls, compile with **`interrupt_before`** or **`interrupt_after`** (replayt step names). Run the first **`invoke`** with initial state, **`config`**, and **`context`**. For the continuation **`invoke`**, pass **`None`** as the graph input, keep the same **`config`** and **`context`**, and reuse the same compiled graph and saver. See **[docs/CHECKPOINT_PERSISTENCE.md](docs/CHECKPOINT_PERSISTENCE.md)** §7 and the tests named above.

## Typing (PEP 561)

Wheels and sdists ship a **`py.typed`** marker under **`replayt_langgraph_bridge`** so type checkers can treat the package as **inline**-typed for the stable names in **`__all__`** (see **[docs/API.md](docs/API.md)** and **[CONTRIBUTING.md](CONTRIBUTING.md)** — **Public API typing**). Stub policy and smoke scope are in **[docs/BACKLOG_PEP561_TYPING_POSTURE.md](docs/BACKLOG_PEP561_TYPING_POSTURE.md)**. After **`uv sync --frozen --extra dev`**, contributors run **`uv run mypy -p replayt_langgraph_bridge`** (same as CI).

## Public API

Supported names are exactly those in `replayt_langgraph_bridge.__all__` (see **[docs/API.md](docs/API.md)** for stability policy and module layout). Summary:

- `compile_replayt_workflow(workflow, *, checkpointer=None, interrupt_before=None, interrupt_after=None, redactor=None, redact=True, strict_redact=False, bridge_logger=None)`: Compile a replayt `Workflow` into a LangGraph `Runnable`. Compile-time misuse raises `BridgeWorkflowCompileError` (subclass of `ValueError`). During `invoke`, undeclared handler transitions raise `BridgeTransitionError` and unknown `replayt_next` targets raise `BridgeRoutingError` (both subclass `BridgeGraphMappingError`, with stable `code` strings; they are **not** `RuntimeError`). See **[docs/GRAPH_CONSTRUCTION_ERRORS.md](docs/GRAPH_CONSTRUCTION_ERRORS.md)**. Step lifecycle and routing errors emit structured records on the logger `replayt_langgraph_bridge` (override with `bridge_logger`) under `LogRecord.replayt_bridge` after redaction per **[docs/LOG_REDACTION.md](docs/LOG_REDACTION.md)**. To silence or tune that logger, use stdlib levels, `logging.NullHandler`, or `propagate=False` (**[docs/API.md](docs/API.md#bridge-logging-silence-and-verbosity)**). Set `REPLAYT_BRIDGE_STRICT_REDACT=1` or pass `strict_redact=True` for stricter masking when the environment does not already require strict mode. `redact=False` disables built-in redaction and issues a runtime warning. **Inbound state:** each step validates channel state before handlers; if you pass a durable checkpointer, it is wrapped so merged `invoke` input is validated before persistence (see **[docs/STATE_PAYLOAD_VALIDATION.md](docs/STATE_PAYLOAD_VALIDATION.md)**). Supported `bridge_state_schema_version` values: `{1}` (omitted means `1`). Limits: nesting depth ≤ 32; ≤ 50_000 walk nodes; ≤ 4_194_304 UTF-8 bytes across all strings in `context`; ≤ 10_000 top-level `context` keys; `replayt_next` length ≤ 1024 after `str()`. Only top-level keys `context`, `replayt_next`, and optional `bridge_state_schema_version` are accepted on full inbound dicts. Optional `interrupt_before` / `interrupt_after` forward to LangGraph `compile` (use replayt step names) when you pause between steps or call `invoke` more than once with the same `thread_id` and a checkpointer (**[docs/CHECKPOINT_PERSISTENCE.md](docs/CHECKPOINT_PERSISTENCE.md)**). Inbound validation failures raise `BridgeStateValidationError` with generic messages.
- `initial_bridge_state(*, context=None)`: Create the initial state dictionary for the bridge graph. The same inbound limits and schema rules apply to `context` before the value is returned; failures raise `BridgeStateValidationError`.
- `ReplaytBridgeState`: `TypedDict` for the bridge channel shape; wire format and limits are normative in **[docs/STATE_PAYLOAD_VALIDATION.md](docs/STATE_PAYLOAD_VALIDATION.md)**.
- `BridgeStateValidationError`: Subclass of `ValueError` for inbound state validation failures (stable, generic `str` values).
- `BridgeWorkflowCompileError`, `BridgeGraphMappingError`, `BridgeTransitionError`, `BridgeRoutingError`: Compile and graph-mapping errors (**[docs/GRAPH_CONSTRUCTION_ERRORS.md](docs/GRAPH_CONSTRUCTION_ERRORS.md)**). `BridgeLargeGraphWarning` (`UserWarning` subclass) may be emitted **once per process** after a successful compile when the workflow has many steps (threshold in **`replayt_langgraph_bridge.graph`**; see the same doc §4.3).
- `RedactorHook`, `get_bridge_logger`, `redact_log_attachment`: Types and helpers for custom redaction and tests (see the log redaction spec).
- `__version__`: The package version.

### Log redaction trade-offs

Default deny keys include LLM-oriented names such as `messages`, `input`, and `content` when the value is a string or list, so bridge logs stay safe by default. Integrators who need raw LLM payloads in logs must supply a custom `redactor` hook (runs after built-in rules) or set `redact=False` and accept the security warning.

## Internal modules

Implementation modules under `replayt_langgraph_bridge` (for example `graph`, `state_validation`) are not a supported import surface for applications. Import the stable names from the package root. See **[docs/API.md](docs/API.md)**.

## Changelog and releases

- **[CHANGELOG.md](CHANGELOG.md)** — notable changes for upgrades (Keep a Changelog layout); **Unreleased** accumulates work in flight; **dependency** and **Breaking** / **Experimental** notes should be explicit for packagers.
- **[docs/RELEASE_CHANGELOG.md](docs/RELEASE_CHANGELOG.md)** — SemVer (including **0.x** expectations), **compatibility signaling**, contributor **Unreleased** workflow, when to edit the changelog, **`vX.Y.Z`** tags, and the manual release checklist. Contributor expectations: **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## Compatibility

- replayt 0.4.x
- LangGraph 1.1.x
- Python 3.11+

See `pyproject.toml` for exact dependency ranges.
