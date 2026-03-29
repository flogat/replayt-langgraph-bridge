"""Replayt boundary (consumer contract) coverage via the LangGraph bridge.

Normative expectations for scope, assertion messages, and ``pytest.raises`` usage:
``docs/REPLAYT_BOUNDARY_TESTS.md``. Checkpoint and ``MemorySaver`` patterns trace to
``docs/CHECKPOINT_PERSISTENCE.md`` §6.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver
from replayt.persistence import JSONLStore
from replayt.runner import Runner
from replayt.workflow import Workflow

from replayt_langgraph_bridge import (
    BridgeRoutingError,
    BridgeTransitionError,
    BridgeWorkflowCompileError,
    compile_replayt_workflow,
    initial_bridge_state,
)


def test_compile_requires_initial_state() -> None:
    """Bridge compile requires ``Workflow.set_initial`` (``workflow.initial_state`` contract)."""
    wf = Workflow("t")
    wf.step("a")(lambda ctx: None)

    with pytest.raises(BridgeWorkflowCompileError, match=r"set_initial") as exc_info:
        compile_replayt_workflow(wf)
    assert isinstance(exc_info.value, ValueError)
    assert type(exc_info.value) is BridgeWorkflowCompileError


def test_compile_rejects_unregistered_initial_step() -> None:
    """``initial_state`` must name a ``@workflow.step`` (GRAPH_CONSTRUCTION_ERRORS / compile contract)."""
    wf = Workflow("init_bad")
    wf.step("a")(lambda ctx: None)
    wf.set_initial("ghost")

    with pytest.raises(
        BridgeWorkflowCompileError,
        match=r"not a registered",
    ) as exc_info:
        compile_replayt_workflow(wf)
    assert exc_info.value.__cause__ is not None


def test_linear_workflow_via_langgraph(tmp_path: Path) -> None:
    """``RunContext.data`` mirrors ``context``; ``JSONLStore``/``Runner`` + ``MemorySaver`` invoke (CHECKPOINT_PERSISTENCE §6)."""
    wf = Workflow("linear")

    @wf.step("first")
    def first(ctx):
        ctx.set("n", 1)
        return "second"

    @wf.step("second")
    def second(ctx):
        ctx.set("n", ctx.get("n", 0) + 1)
        return None

    wf.set_initial("first")
    wf.note_transition("first", "second")

    store_path = tmp_path / "events.jsonl"
    store = JSONLStore(store_path)
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())

    graph = compile_replayt_workflow(wf, checkpointer=MemorySaver())
    out = graph.invoke(
        initial_bridge_state(context={"seed": True}),
        config={"configurable": {"thread_id": "t1"}},
        context={"runner": runner},
    )

    assert out["context"]["seed"] is True, (
        "replayt boundary: initial LangGraph context must shallow-merge into RunContext.data"
    )
    assert out["context"]["n"] == 2, (
        "replayt boundary: RunContext.data carries cumulative ctx.set across linear steps"
    )
    assert out["replayt_next"] == "", (
        "replayt boundary: terminal handler return must normalize to empty replayt_next (graph end)"
    )


def test_resume_second_invoke_uses_memory_checkpointer(tmp_path: Path) -> None:
    """Second ``invoke`` continues the same ``thread_id`` from ``MemorySaver`` (CHECKPOINT_PERSISTENCE §6)."""
    wf = Workflow("resume_two_invoke")

    @wf.step("first")
    def first(ctx):
        ctx.set("phase", 1)
        return "second"

    @wf.step("second")
    def second(ctx):
        ctx.set("phase", ctx.get("phase", 0) + 10)
        return None

    wf.set_initial("first")
    wf.note_transition("first", "second")

    store_path = tmp_path / "resume.jsonl"
    store = JSONLStore(store_path)
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())

    saver = MemorySaver()
    graph = compile_replayt_workflow(
        wf, checkpointer=saver, interrupt_before=["second"]
    )
    cfg = {"configurable": {"thread_id": "resume-two"}}

    out1 = graph.invoke(
        initial_bridge_state(context={"seed": True}),
        config=cfg,
        context={"runner": runner},
    )
    assert out1["context"]["seed"] is True, (
        "replayt boundary: first invoke must preserve merged LangGraph context in bridge state"
    )
    assert out1["context"]["phase"] == 1, (
        "replayt boundary: first step must persist RunContext.data through checkpoint boundary"
    )
    assert out1["replayt_next"] == "second", (
        "replayt boundary: interrupt_before second must leave replayt_next pointing at next step"
    )
    assert len(list(saver.list(cfg))) >= 1, (
        "replayt boundary: MemorySaver must persist at least one checkpoint for resume"
    )

    out2 = graph.invoke(None, config=cfg, context={"runner": runner})
    assert out2["context"]["phase"] == 11, (
        "replayt boundary: resumed invoke must run second step and accumulate RunContext.data"
    )
    assert out2["replayt_next"] == "", (
        "replayt boundary: terminal step must clear replayt_next after resume"
    )
    assert out2["context"]["seed"] is True, (
        "replayt boundary: resumed run must keep original context keys from first invoke"
    )


def test_resume_second_invoke_interrupt_after_first_uses_memory_checkpointer(
    tmp_path: Path,
) -> None:
    """``interrupt_after`` + second ``invoke`` on the same ``thread_id`` (CHECKPOINT_PERSISTENCE §6).

    Spec: ``docs/BACKLOG_HITL_INTERRUPT_COOKBOOK.md`` (backlog ``4b64a655-bb06-49e5-8912-61b06626a034``).
    Observable first-``invoke`` state matches LangGraph 1.1.x with ``interrupt_after=["first"]``.
    """
    wf = Workflow("resume_two_invoke_after")

    @wf.step("first")
    def first(ctx):
        ctx.set("phase", 1)
        return "second"

    @wf.step("second")
    def second(ctx):
        ctx.set("phase", ctx.get("phase", 0) + 10)
        return None

    wf.set_initial("first")
    wf.note_transition("first", "second")

    store_path = tmp_path / "resume_after.jsonl"
    store = JSONLStore(store_path)
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())

    saver = MemorySaver()
    graph = compile_replayt_workflow(
        wf, checkpointer=saver, interrupt_after=["first"]
    )
    cfg = {"configurable": {"thread_id": "resume-after-first"}}

    out1 = graph.invoke(
        initial_bridge_state(context={"seed": True}),
        config=cfg,
        context={"runner": runner},
    )
    assert out1["context"]["seed"] is True, (
        "replayt boundary: first invoke must preserve merged LangGraph context in bridge state"
    )
    assert out1["context"]["phase"] == 1, (
        "replayt boundary: interrupt_after first must run first step and persist RunContext.data"
    )
    assert out1["replayt_next"] == "second", (
        "replayt boundary: interrupt_after first must leave replayt_next at the next step"
    )
    assert len(list(saver.list(cfg))) >= 1, (
        "replayt boundary: MemorySaver must persist at least one checkpoint for resume"
    )

    out2 = graph.invoke(None, config=cfg, context={"runner": runner})
    assert out2["context"]["phase"] == 11, (
        "replayt boundary: resumed invoke must run second step and accumulate RunContext.data"
    )
    assert out2["replayt_next"] == "", (
        "replayt boundary: terminal step must clear replayt_next after resume"
    )
    assert out2["context"]["seed"] is True, (
        "replayt boundary: resumed run must keep original context keys from first invoke"
    )


def test_unknown_next_state_raises(tmp_path: Path) -> None:
    """Routing rejects unknown next step; ``MemorySaver`` present (CHECKPOINT_PERSISTENCE §6 baseline)."""
    wf = Workflow("bad")

    @wf.step("a")
    def a(ctx):
        return "nonexistent"

    wf.set_initial("a")

    store = JSONLStore(tmp_path / "e.jsonl")
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())

    graph = compile_replayt_workflow(wf, checkpointer=MemorySaver())
    with pytest.raises(BridgeRoutingError, match=r"unknown next state") as exc_info:
        graph.invoke(
            initial_bridge_state(),
            config={"configurable": {"thread_id": "t2"}},
            context={"runner": runner},
        )
    assert exc_info.value.code == "unknown_next"
    assert type(exc_info.value) is BridgeRoutingError


def test_declared_edge_violation_raises(tmp_path: Path) -> None:
    """Declared-edge violation; ``MemorySaver`` present (CHECKPOINT_PERSISTENCE §6 baseline)."""
    wf = Workflow("edges")

    @wf.step("a")
    def a(ctx):
        return "b"

    @wf.step("b")
    def b(ctx):
        return None

    wf.set_initial("a")
    wf.note_transition("a", "c")  # declares wrong edge — handler returns "b"

    store = JSONLStore(tmp_path / "e2.jsonl")
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())

    graph = compile_replayt_workflow(wf, checkpointer=MemorySaver())
    with pytest.raises(BridgeTransitionError, match=r"undeclared transition") as exc_info:
        graph.invoke(
            initial_bridge_state(),
            config={"configurable": {"thread_id": "t3"}},
            context={"runner": runner},
        )
    assert exc_info.value.code == "undeclared_transition"
    assert type(exc_info.value) is BridgeTransitionError
