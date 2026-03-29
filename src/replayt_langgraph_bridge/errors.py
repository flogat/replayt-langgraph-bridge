"""Public exceptions for graph compilation and routing (``docs/GRAPH_CONSTRUCTION_ERRORS.md``)."""

from __future__ import annotations

from typing import ClassVar, Literal

InvokeContextErrorCode = Literal["missing_runner", "runner_workflow_mismatch"]


class BridgeGraphMappingError(Exception):
    """Base class for failures mapping handler returns to the workflow graph (routing / edges)."""

    code: ClassVar[str] = ""


class BridgeWorkflowCompileError(ValueError):
    """Raised when a :class:`~replayt.workflow.Workflow` cannot be compiled (initial step contract)."""


class BridgeTransitionError(BridgeGraphMappingError):
    """Handler return is not allowed by declared edges (:meth:`~replayt.workflow.Workflow.allows_transition`)."""

    code: ClassVar[Literal["undeclared_transition"]] = "undeclared_transition"


class BridgeRoutingError(BridgeGraphMappingError):
    """``replayt_next`` names a step that is not registered on the workflow."""

    code: ClassVar[Literal["unknown_next"]] = "unknown_next"


class BridgeInvokeContextError(Exception):
    """Raised when :meth:`~langgraph.graph.state.CompiledStateGraph.invoke` context omits or misconfigures the replayt
    :class:`~replayt.runner.Runner` for the compiled :class:`~replayt.workflow.Workflow`.

    ``code`` is ``\"missing_runner\"`` or ``\"runner_workflow_mismatch\"`` (see ``docs/GRAPH_CONSTRUCTION_ERRORS.md`` §3.4).
    """

    code: InvokeContextErrorCode

    def __init__(self, message: str, *, code: InvokeContextErrorCode) -> None:
        super().__init__(message)
        self.code = code


class BridgeLargeGraphWarning(UserWarning):
    """Emitted at most once per interpreter process when ``compile_replayt_workflow`` builds a very large graph.

    Filter with ``warnings.filterwarnings`` on this category, or silence stdlib warning display. See
    ``docs/GRAPH_CONSTRUCTION_ERRORS.md`` §4.3.
    """
