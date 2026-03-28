"""Public exceptions for graph compilation and routing (``docs/GRAPH_CONSTRUCTION_ERRORS.md``)."""

from __future__ import annotations

from typing import ClassVar, Literal


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
