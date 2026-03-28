"""Compile a replayt :class:`~replayt.workflow.Workflow` into a LangGraph :class:`~langgraph.graph.state.StateGraph`."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime
from langgraph.types import Checkpointer
from replayt.runner import RunContext, Runner
from replayt.workflow import Workflow
from typing_extensions import NotRequired, TypedDict

from replayt_langgraph_bridge.bridge_log import emit_bridge_record, get_bridge_logger
from replayt_langgraph_bridge.redaction import RedactorHook
from replayt_langgraph_bridge.state_validation import (
    BridgeValidatingCheckpointSaver,
    validate_inbound_bridge_state,
)


def _merge_context(
    left: dict[str, Any], right: dict[str, Any] | None
) -> dict[str, Any]:
    if right is None:
        return left
    return {**left, **right}


class ReplaytBridgeState(TypedDict):
    """LangGraph channel state mirrored with :class:`~replayt.runner.RunContext` ``data``."""

    context: Annotated[dict[str, Any], _merge_context]
    replayt_next: str
    bridge_state_schema_version: NotRequired[int]


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


def initial_bridge_state(
    *, context: dict[str, Any] | None = None
) -> ReplaytBridgeState:
    """Build input state for the first :meth:`~langgraph.graph.state.CompiledStateGraph.invoke` call.

    Inbound ``context`` is validated as untrusted input before returning. Supported wire schema
    versions: ``{1}`` (``bridge_state_schema_version``; omitted means ``1``). Limits: nesting depth
    ≤ 32; ≤ 50_000 walk nodes (dict keys, list/tuple/set items); ≤ 4_194_304 UTF-8 bytes across all
    strings in ``context``; ≤ 10_000 top-level ``context`` keys; ``replayt_next`` length ≤ 1024 after
    ``str()`` (here always ``\"\"``). On failure, raises :exc:`~replayt_langgraph_bridge.BridgeStateValidationError`
    with a generic message; see ``docs/STATE_PAYLOAD_VALIDATION.md``.
    """

    state: ReplaytBridgeState = {
        "context": dict(context) if context else {},
        "replayt_next": "",
    }
    validate_inbound_bridge_state(state)
    return state


def _normalize_next(handler_result: str | None) -> str:
    if handler_result in (None, ""):
        return ""
    return str(handler_result)


def _make_step_node(
    step_name: str,
    workflow: Workflow,
    merged_llm: dict[str, Any],
    *,
    bridge_logger: logging.Logger,
    redactor: RedactorHook | None,
    redact: bool,
    strict_redact: bool,
):
    def step_node(
        state: ReplaytBridgeState, *, runtime: Runtime[ReplaytBridgeContext]
    ) -> dict[str, Any]:
        validate_inbound_bridge_state(state, logger=bridge_logger)
        runner = runtime.context["runner"]
        run_id = getattr(runner, "run_id", None)
        runner._current_state = step_name
        ctx = RunContext(runner, llm_defaults=merged_llm or None)
        ctx.data.clear()
        ctx.data.update(state["context"])
        handler = workflow.get_handler(step_name)
        try:
            nxt = handler(ctx)
        except Exception:
            emit_bridge_record(
                bridge_logger,
                logging.ERROR,
                "replayt bridge step handler raised",
                {
                    "event": "step_handler_error",
                    "event_type": "step_handler_error",
                    "step": step_name,
                    "run_id": run_id,
                    "context": dict(ctx.data),
                },
                redact=redact,
                strict_redact=strict_redact,
                redactor=redactor,
            )
            raise
        if not workflow.allows_transition(step_name, nxt):
            allowed = [dst for src, dst in workflow.edges() if src == step_name]
            emit_bridge_record(
                bridge_logger,
                logging.ERROR,
                "replayt bridge transition rejected",
                {
                    "event": "transition_invalid",
                    "event_type": "transition_invalid",
                    "step": step_name,
                    "to_step": nxt,
                    "run_id": run_id,
                    "allowed": allowed,
                    "context": dict(ctx.data),
                },
                redact=redact,
                strict_redact=strict_redact,
                redactor=redactor,
            )
            raise RuntimeError(
                f"Step {step_name!r} returned undeclared transition {nxt!r}; allowed={allowed}"
            )
        normalized = _normalize_next(nxt)
        emit_bridge_record(
            bridge_logger,
            logging.INFO,
            "replayt bridge step completed",
            {
                "event": "step_completed",
                "event_type": "step_completed",
                "step": step_name,
                "replayt_next": normalized,
                "run_id": run_id,
                "context": dict(ctx.data),
            },
            redact=redact,
            strict_redact=strict_redact,
            redactor=redactor,
        )
        return {"context": dict(ctx.data), "replayt_next": normalized}

    step_node.__name__ = f"replayt_step_{step_name}"
    return step_node


def _route_from(
    step_name: str,
    step_names: set[str],
    *,
    bridge_logger: logging.Logger,
    redactor: RedactorHook | None,
    redact: bool,
    strict_redact: bool,
):
    def route(state: ReplaytBridgeState):
        nxt = state.get("replayt_next", "")
        if nxt in ("", None):
            return END
        if nxt not in step_names:
            emit_bridge_record(
                bridge_logger,
                logging.ERROR,
                "replayt bridge unknown next state",
                {
                    "event": "unknown_next",
                    "event_type": "unknown_next",
                    "from_step": step_name,
                    "to_step": nxt,
                    "expected": sorted(step_names),
                },
                redact=redact,
                strict_redact=strict_redact,
                redactor=redactor,
            )
            raise RuntimeError(
                f"After step {step_name!r}, unknown next state {nxt!r}; expected one of {sorted(step_names)!r} or end"
            )
        return nxt

    return route


def compile_replayt_workflow(
    workflow: Workflow,
    *,
    checkpointer: Checkpointer | None = None,
    redactor: RedactorHook | None = None,
    redact: bool = True,
    strict_redact: bool = False,
    bridge_logger: logging.Logger | None = None,
) -> CompiledStateGraph[
    ReplaytBridgeState, ReplaytBridgeContext, ReplaytBridgeState, ReplaytBridgeState
]:
    """Wire each replayt step to a LangGraph node; route by handler return value (replayt_next).

    Pass a configured :class:`~replayt.runner.Runner` (same ``workflow`` and ``store`` you use for replayt) via
    ``invoke(..., context={"runner": runner})``. Set ``runner.run_id`` before invoking if handlers emit events.

    Bridge lifecycle events are logged on the logger named ``replayt_langgraph_bridge`` (or ``bridge_logger``)
    with structured metadata under ``LogRecord.replayt_bridge`` after redaction per ``docs/LOG_REDACTION.md``.
    Set ``REPLAYT_BRIDGE_STRICT_REDACT=1`` or pass ``strict_redact=True`` for stricter masking (most restrictive wins
    when the env enables strict). ``redact=False`` disables built-in redaction and emits a runtime warning.

    Inbound :class:`ReplaytBridgeState` is validated on every bridge step before handlers run: schema
    version ``{1}`` (``bridge_state_schema_version`` omitted means ``1``), nesting depth ≤ 32, walk
    nodes ≤ 50_000, total UTF-8 string bytes in ``context`` ≤ 4_194_304, top-level ``context`` keys
    ≤ 10_000, ``replayt_next`` length ≤ 1024 after ``str()``; only top-level keys ``context``,
    ``replayt_next``, and optional ``bridge_state_schema_version`` are allowed. Failures raise
    :exc:`~replayt_langgraph_bridge.BridgeStateValidationError`. Normative detail:
    ``docs/STATE_PAYLOAD_VALIDATION.md``.
    """

    if not workflow.initial_state:
        raise ValueError(
            "workflow.initial_state must be set (call workflow.set_initial)"
        )

    names = workflow.step_names()
    try:
        workflow.get_handler(workflow.initial_state)
    except KeyError as e:
        raise ValueError(
            f"initial_state {workflow.initial_state!r} is not a registered @workflow.step"
        ) from e

    name_set = set(names)
    merged_llm = _merged_llm_defaults(workflow)
    log = bridge_logger if bridge_logger is not None else get_bridge_logger()

    graph: StateGraph[
        ReplaytBridgeState, ReplaytBridgeContext, ReplaytBridgeState, ReplaytBridgeState
    ] = StateGraph(
        state_schema=ReplaytBridgeState,
        context_schema=ReplaytBridgeContext,
    )

    path_map: dict[str, str] = {n: n for n in names}
    path_map[END] = END

    for name in names:
        graph.add_node(
            name,
            _make_step_node(
                name,
                workflow,
                merged_llm,
                bridge_logger=log,
                redactor=redactor,
                redact=redact,
                strict_redact=strict_redact,
            ),
        )
        graph.add_conditional_edges(
            name,
            _route_from(
                name,
                name_set,
                bridge_logger=log,
                redactor=redactor,
                redact=redact,
                strict_redact=strict_redact,
            ),
            path_map,
        )

    graph.add_edge(START, workflow.initial_state)

    effective_checkpointer = checkpointer
    if (
        effective_checkpointer is not None
        and effective_checkpointer not in (True, False)
        and not isinstance(effective_checkpointer, BridgeValidatingCheckpointSaver)
    ):
        effective_checkpointer = BridgeValidatingCheckpointSaver(
            effective_checkpointer, logger=log
        )

    return graph.compile(checkpointer=effective_checkpointer)
