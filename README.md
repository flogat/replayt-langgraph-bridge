# replayt-langgraph-bridge

LangGraph adapter mapping replayt workflow states to graph nodes and checkpoints.

This project builds on **replayt** as a **LangGraph framework bridge**. Read
**[docs/REPLAYT_ECOSYSTEM_IDEA.md](docs/REPLAYT_ECOSYSTEM_IDEA.md)** for the primary pattern and compatibility stance, then
**[docs/MISSION.md](docs/MISSION.md)** for users, scope, success metrics, and version intent.

## Design principles

**[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** covers **replayt** compatibility, versioning, integrator security
expectations, and (for showcases) **LLM** boundaries.

For a detailed threat model on checkpoint and state data, see **[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)**. For the **log redaction** contract (defaults, strict mode, integrator hook) for bridge-originated structured logs, see **[docs/LOG_REDACTION.md](docs/LOG_REDACTION.md)**. For **inbound bridge state** validation (planned hardening: size limits, schema version, malformed nesting), see **[docs/STATE_PAYLOAD_VALIDATION.md](docs/STATE_PAYLOAD_VALIDATION.md)**.

## Dependency strategy

This project follows a deliberate **dependency and pin policy** so downstream installs do not pick up unexpected **major** upgrades of **replayt** or **LangGraph**.

- **Runtime** (installed with `pip install replayt-langgraph-bridge`): `replayt>=0.4.0,<0.5` and `langgraph>=1.1.0,<1.2`, declared in **`pyproject.toml`** with short comments explaining bounds.
- **Minimum supported** vs **upper bounds**: Lower bounds reflect features and support posture; `< next-major` caps automatic upgrades until maintainers validate a new line.
- **What CI exercises**: **Python** 3.11 and 3.12 jobs install the package with **`[dev]`** and run **pytest**; **replayt** and **langgraph** resolve to the **latest versions allowed by those ranges** on each run (no separate lockfile today).
- **Contributor install**: `pip install -e ".[dev]"` pulls **pytest**, **ruff**, and **pip-audit** only via the **`dev`** optional extra—never as default runtime deps.
- **Upstream majors or risky bumps**: Use the **Compatibility Update** issue template (`.github/ISSUE_TEMPLATE/compatibility_update.md`) and follow the maintainer checklist in **[docs/DESIGN_PRINCIPLES.md#dependency-and-pin-policy](docs/DESIGN_PRINCIPLES.md#dependency-and-pin-policy)**.

The full policy (selection rules, LangGraph major rollout risk, and builder-facing acceptance criteria) lives in **[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)**.

## Reference documentation (optional)

This checkout does not yet include [`docs/reference-documentation/`](docs/reference-documentation/). You can add markdown
copies of upstream replayt documentation there for offline review or agent context.

## Installation

```bash
pip install replayt-langgraph-bridge
```

### Secrets handling
**Important**: Never commit secrets to version control. Store API keys and tokens in environment variables.

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
from replayt_langgraph_bridge import compile_replayt_workflow

# Read secrets from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# Use the key in your workflow
# ... (your workflow code here)
```

For the complete secrets policy, see **[docs/DESIGN_PRINCIPLES.md#secrets-policy](docs/DESIGN_PRINCIPLES.md#secrets-policy)**.

## Usage

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

## Public API

- `compile_replayt_workflow(workflow, *, checkpointer=None, redactor=None, redact=True, strict_redact=False, bridge_logger=None)`: Compile a replayt `Workflow` into a LangGraph `Runnable`. Step lifecycle and routing errors emit structured records on the logger `replayt_langgraph_bridge` (override with `bridge_logger`) under `LogRecord.replayt_bridge` after redaction per **[docs/LOG_REDACTION.md](docs/LOG_REDACTION.md)**. Set `REPLAYT_BRIDGE_STRICT_REDACT=1` or pass `strict_redact=True` for stricter masking when the environment does not already require strict mode. `redact=False` disables built-in redaction and issues a runtime warning. **Inbound state hardening** (max sizes, `bridge_state_schema_version`, safe rejection before handlers/checkpoint writes) is specified in **[docs/STATE_PAYLOAD_VALIDATION.md](docs/STATE_PAYLOAD_VALIDATION.md)** and is implemented in a dedicated backlog—not all limits are enforced in code yet.
- `initial_bridge_state(*, context=None)`: Create the initial state dictionary for the bridge graph. The `context` dict crosses the **untrusted-input** boundary described in **[docs/STATE_PAYLOAD_VALIDATION.md](docs/STATE_PAYLOAD_VALIDATION.md)** (supported schema versions, numeric limits, and test obligations live there).
- `RedactorHook`, `get_bridge_logger`, `redact_log_attachment`: Types and helpers for custom redaction and tests (see the log redaction spec).
- `__version__`: The package version.

### Log redaction trade-offs

Default deny keys include LLM-oriented names such as `messages`, `input`, and `content` when the value is a string or list, so bridge logs stay safe by default. Integrators who need raw LLM payloads in logs must supply a custom `redactor` hook (runs after built-in rules) or set `redact=False` and accept the security warning.

## Internal Modules

The `graph` module contains internal implementation details and is not part of the public API. It may change without notice.

## Compatibility

- replayt 0.4.x
- LangGraph 1.1.x
- Python 3.11+

See `pyproject.toml` for exact dependency ranges.
