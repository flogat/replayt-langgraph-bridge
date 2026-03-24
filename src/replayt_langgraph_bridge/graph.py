"""Compile a replayt :class:`~replayt.workflow.Workflow` into a LangGraph :class:`~langgraph.graph.state.StateGraph`."""

from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime
from langgraph.types import Checkpointer
from replayt.runner import RunContext, Runner
from replayt.workflow import Workflow
from typing_extensions import TypedDict


def _merge_context(left: dict[str, Any], right: dict[str, Any] | None) -> dict[str, Any]:
    if right is None:
        return left
    return {**left, **right}


class ReplaytBridgeState(TypedDict):
    """LangGraph channel state mirrored with :class:`~replayt.runner.RunContext` ``data``."""

    context: Annotated[dict[str, Any], _merge_context]
    replayt_next: str


class ReplaytBridgeContext(TypedDict):
    """Runtime context passed to :meth:`~langgraph.graph.state.CompiledStateGraph.invoke` as ``context=``."""

    runner: Runner


def _merged_llm_defaults(workflow: Workflow) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if workflow.llm_defaults:
        merged.update(workflow.llm_defaults)
    meta_ld = (workflow.meta or {}).get("llm_defaults")
    if isinstance(meta_ld, dict):
        merged.update(meta_ld)
    return merged


def initial_bridge_state(*, context: dict[str, Any] | None = None) -> ReplaytBridgeState:
    """Build input state for the first :meth:`~langgraph.graph.state.CompiledStateGraph.invoke` call."""

    return {"context": dict(context) if context else {}, "replayt_next": ""}


def _normalize_next(handler_result: str | None) -> str:
    if handler_result in (None, ""):
        return ""
    return str(handler_result)


def _make_step_node(step_name: str, workflow: Workflow, merged_llm: dict[str, Any]):
    def step_node(state: ReplaytBridgeState, *, runtime: Runtime[ReplaytBridgeContext]) -> dict[str, Any]:
        runner = runtime.context["runner"]
        runner._current_state = step_name
        ctx = RunContext(runner, llm_defaults=merged_llm or None)
        ctx.data.clear()
        ctx.data.update(state["context"])
        handler = workflow.get_handler(step_name)
        nxt = handler(ctx)
        if not workflow.allows_transition(step_name, nxt):
            allowed = [dst for src, dst in workflow.edges() if src == step_name]
            raise RuntimeError(
                f"Step {step_name!r} returned undeclared transition {nxt!r}; allowed={allowed}"
            )
        return {"context": dict(ctx.data), "replayt_next": _normalize_next(nxt)}

    step_node.__name__ = f"replayt_step_{step_name}"
    return step_node


def _route_from(step_name: str, workflow: Workflow, step_names: set[str]):
    def route(state: ReplaytBridgeState):
        nxt = state.get("replayt_next", "")
        if nxt in ("", None):
            return END
        if nxt not in step_names:
            raise RuntimeError(
                f"After step {step_name!r}, unknown next state {nxt!r}; expected one of {sorted(step_names)!r} or end"
            )
        return nxt

    return route


def compile_replayt_workflow(
    workflow: Workflow,
    *,
    checkpointer: Checkpointer | None = None,
) -> CompiledStateGraph[ReplaytBridgeState, ReplaytBridgeContext, ReplaytBridgeState, ReplaytBridgeState]:
    """Wire each replayt step to a LangGraph node; route by handler return value (replayt_next).

    Pass a configured :class:`~replayt.runner.Runner` (same ``workflow`` and ``store`` you use for replayt) via
    ``invoke(..., context={"runner": runner})``. Set ``runner.run_id`` before invoking if handlers emit events.
    """

    if not workflow.initial_state:
        raise ValueError("workflow.initial_state must be set (call workflow.set_initial)")

    names = workflow.step_names()
    try:
        workflow.get_handler(workflow.initial_state)
    except KeyError as e:
        raise ValueError(
            f"initial_state {workflow.initial_state!r} is not a registered @workflow.step"
        ) from e

    name_set = set(names)
    merged_llm = _merged_llm_defaults(workflow)

    graph: StateGraph[ReplaytBridgeState, ReplaytBridgeContext, ReplaytBridgeState, ReplaytBridgeState] = StateGraph(
        state_schema=ReplaytBridgeState,
        context_schema=ReplaytBridgeContext,
    )

    path_map: dict[str, str] = {n: n for n in names}
    path_map[END] = END

    for name in names:
        graph.add_node(name, _make_step_node(name, workflow, merged_llm))
        graph.add_conditional_edges(name, _route_from(name, workflow, name_set), path_map)

    graph.add_edge(START, workflow.initial_state)

    return graph.compile(checkpointer=checkpointer)
