# replayt-langgraph-bridge

LangGraph adapter mapping replayt workflow states to graph nodes and checkpoints.

<<<<<<< HEAD
This project builds on **replayt** as a **LangGraph framework bridge**. Read
**[docs/REPLAYT_ECOSYSTEM_IDEA.md](docs/REPLAYT_ECOSYSTEM_IDEA.md)** for the primary pattern and compatibility stance, then
**[docs/MISSION.md](docs/MISSION.md)** for users, scope, success metrics, and version intent.

## Design principles

**[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** covers **replayt** compatibility, versioning, integrator security
expectations, and (for showcases) **LLM** boundaries.

For a detailed threat model on checkpoint and state data, see **[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)**.

<<<<<<< HEAD
## Compatibility matrix

| Component | Supported versions | Notes |
|-----------|-------------------|-------|
| replayt | 0.4.x | `replayt>=0.4.0,<0.5` in `pyproject.toml` |
| LangGraph | 1.1.x | `langgraph>=1.1.0,<1.2` in `pyproject.toml` |
| Python | 3.11+ | `requires-python = ">=3.11"` in `pyproject.toml` |

**Version policy:**
- Patch versions within the supported minor version range are automatically compatible
- Minor version bumps require explicit testing and may require bridge updates
- Major version bumps are breaking changes and will require significant bridge updates
=======
## Dependency Strategy

This project follows a deliberate dependency and pin policy to ensure stability for downstream teams:

- **Runtime dependencies**: `replayt>=0.4.0,<0.5` and `langgraph>=1.1.0,<1.2`
- **Version selection**: Minimum supported versions based on tested functionality; upper bounds prevent automatic breaking changes
- **Testing matrix**: CI runs against specific versions to ensure compatibility
- **Breaking changes**: Process established for monitoring, testing, and documenting upstream releases

See **[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** for the complete dependency policy.
>>>>>>> mc/backlog-befc42a4

## Reference documentation (optional)

This checkout does not yet include [`docs/reference-documentation/`](docs/reference-documentation/). You can add markdown
copies of upstream replayt documentation there for offline review or agent context.

## Quick start
=======
## Installation
>>>>>>> mc/backlog-4542c070

```bash
pip install replayt-langgraph-bridge
```

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

- `compile_replayt_workflow(workflow, *, checkpointer=None, ...)`: Compile a replayt `Workflow` into a LangGraph `Runnable`.
- `initial_bridge_state(*, context=None)`: Create the initial state dictionary for the bridge graph.
- `__version__`: The package version.

## Internal Modules

The `graph` module contains internal implementation details and is not part of the public API. It may change without notice.

## Compatibility

- replayt 0.4.x
- LangGraph 1.1.x
- Python 3.11+

See `pyproject.toml` for exact dependency ranges.
