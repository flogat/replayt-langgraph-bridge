# replayt-langgraph-bridge

LangGraph adapter mapping replayt workflow states to graph nodes and checkpoints.

This project builds on **replayt** as a **LangGraph framework bridge**. Read
**[docs/REPLAYT_ECOSYSTEM_IDEA.md](docs/REPLAYT_ECOSYSTEM_IDEA.md)** for the primary pattern and compatibility stance, then
**[docs/MISSION.md](docs/MISSION.md)** for users, scope, success metrics, and version intent.

## Design principles

**[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** covers **replayt** compatibility, versioning, integrator security
expectations, and (for showcases) **LLM** boundaries.

For a detailed threat model on checkpoint and state data, see **[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)**.

## Dependency Strategy

This project follows a deliberate dependency and pin policy to ensure stability for downstream teams:

- **Runtime dependencies**: `replayt>=0.4.0,<0.5` and `langgraph>=1.1.0,<1.2`
- **Version selection**: Minimum supported versions based on tested functionality; upper bounds prevent automatic breaking changes
- **Testing matrix**: CI runs against specific versions to ensure compatibility
- **Breaking changes**: Process established for monitoring, testing, and documenting upstream releases

See **[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** for the complete dependency policy.

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
