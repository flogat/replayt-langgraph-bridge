"""
replayt-langgraph-bridge: LangGraph adapter for replayt workflows.

This package provides a bridge to run replayt workflows inside LangGraph graphs,
handling state mapping and checkpoints.

Public API (see ``docs/API.md`` for stability policy and full layout; ``__all__`` below is canonical):
- ``compile_replayt_workflow``: Compile a replayt Workflow into a LangGraph Runnable.
- ``initial_bridge_state``: Create the initial state for a replayt bridge graph; inbound ``context`` is validated
  (schema ``{1}``, depth ≤ 32, walk nodes ≤ 50_000, string bytes ≤ 4_194_304, top-level keys ≤ 10_000,
  ``replayt_next`` ≤ 1024 after ``str()``; see ``docs/STATE_PAYLOAD_VALIDATION.md``).
- ``ReplaytBridgeState``: TypedDict for LangGraph channel state mirrored with replayt ``RunContext.data``.
- ``BridgeStateValidationError``: Raised when inbound bridge state fails validation (generic message strings).
- ``RedactorHook`` / ``get_bridge_logger`` / ``redact_log_attachment``: Log redaction and bridge logging helpers.
- ``__version__``: Package version.

Internal modules (not part of the supported import surface for applications):
- ``graph``, ``state_validation``, ``redaction``, ``bridge_log``: implementation details; may change without notice.
"""

from .bridge_log import get_bridge_logger
from .graph import (
    ReplaytBridgeState,
    compile_replayt_workflow,
    initial_bridge_state,
)
from .state_validation import BridgeStateValidationError
from .redaction import RedactorHook, redact_log_attachment

__version__ = "0.1.0"

__all__ = [
    "BridgeStateValidationError",
    "ReplaytBridgeState",
    "RedactorHook",
    "compile_replayt_workflow",
    "get_bridge_logger",
    "initial_bridge_state",
    "redact_log_attachment",
    "__version__",
]
