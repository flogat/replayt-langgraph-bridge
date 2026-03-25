# replayt-langgraph-bridge

LangGraph adapter mapping replayt workflow states to graph nodes and checkpoints.

## Installation

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
