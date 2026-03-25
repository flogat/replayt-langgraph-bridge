from __future__ import annotations

from typing import Any, Dict, Set, TypedDict, Optional

from langgraph.graph import StateGraph, END

from replayt.workflow import Workflow
from replayt.runner import Runner


class ReplaytBridgeState(TypedDict):
    context: Dict[str, Any]
    replayt_next: str


class Context:
    """Proxy context for replayt step handlers."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value


def initial_bridge_state(context: Optional[Dict[str, Any]] = None) -> ReplaytBridgeState:
    return {
        "context": context or {},
        "replayt_next": "",
    }


def compile_replayt_workflow(
    wf: Workflow, checkpointer: Optional[Any] = None
) -> StateGraph[ReplaytBridgeState]:
    if not hasattr(wf, "_initial") or wf._initial is None:
        raise ValueError("Workflow must have an initial state set with set_initial()")

    def entry(state: ReplaytBridgeState) -> ReplaytBridgeState:
        return {
            "context": state["context"],
            "replayt_next": wf._initial,
        }

    def execute_next(state: ReplaytBridgeState) -> ReplaytBridgeState:
        current_step: str = state["replayt_next"]
        handler = wf._steps[current_step]
        ctx_data = dict(state["context"])
        ctx = Context(ctx_data)
        next_step = handler(ctx)
        if next_step is None:
            next_step = ""
        new_context = ctx._data

        if next_step:
            if next_step not in wf._steps:
                raise RuntimeError(f"unknown next state '{next_step}'")
            allowed: Set[str] = wf._transitions.get(current_step, set())
            if next_step not in allowed:
                raise RuntimeError(
                    f"undeclared transition {current_step!r} -> {next_step!r}; allowed: {sorted(allowed)}"
                )

        return {
            "context": new_context,
            "replayt_next": next_step,
        }

    def should_continue(state: ReplaytBridgeState) -> str:
        return "continue" if state["replayt_next"] else "end"

    graph = StateGraph(ReplaytBridgeState, checkpointer=checkpointer)
    graph.add_node("entry", entry)
    graph.add_node("execute_next", execute_next)
    graph.set_entry_point("entry")
    graph.add_edge("entry", "execute_next")
    graph.add_conditional_edges(
        "execute_next",
        should_continue,
        {"continue": "execute_next", "end": END},
    )
    return graph.compile()
