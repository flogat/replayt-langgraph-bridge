"""
replayt-langgraph-bridge: LangGraph adapter for replayt workflows.

This package provides a bridge to run replayt workflows inside LangGraph graphs,
handling state mapping and checkpoints.

Public API:
- `compile_replayt_workflow`: Compile a replayt Workflow into a LangGraph Runnable.
- `initial_bridge_state`: Create the initial state for a replayt bridge graph.
- `RedactorHook` / `get_bridge_logger` / `redact_log_attachment`: Log redaction and bridge logging helpers.
- `__version__`: Package version.

Internal modules (not part of the public API):
- `graph`: Internal implementation details for graph compilation and state handling.
"""

from .bridge_log import get_bridge_logger
from .graph import (
    ReplaytBridgeState,
    compile_replayt_workflow,
    initial_bridge_state,
)
from .redaction import RedactorHook, redact_log_attachment

__version__ = "0.1.0"

__all__ = [
    "ReplaytBridgeState",
    "RedactorHook",
    "compile_replayt_workflow",
    "get_bridge_logger",
    "initial_bridge_state",
    "redact_log_attachment",
    "__version__",
]
