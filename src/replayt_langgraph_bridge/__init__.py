<<<<<<< HEAD
"""
replayt-langgraph-bridge: LangGraph adapter for replayt workflows.

This package provides a bridge to run replayt workflows inside LangGraph graphs,
handling state mapping and checkpoints.

Public API:
- `compile_replayt_workflow`: Compile a replayt Workflow into a LangGraph Runnable.
- `initial_bridge_state`: Create the initial state for a replayt bridge graph.
- `__version__`: Package version.

Internal modules (not part of the public API):
- `graph`: Internal implementation details for graph compilation and state handling.
"""

from .graph import (
=======
from .graph import (
    ReplaytBridgeState,
>>>>>>> mc/backlog-591f8168
    compile_replayt_workflow,
    initial_bridge_state,
)

__version__ = "0.1.0"

__all__ = [
<<<<<<< HEAD
=======
    "ReplaytBridgeState",
>>>>>>> mc/backlog-591f8168
    "compile_replayt_workflow",
    "initial_bridge_state",
    "__version__",
]
