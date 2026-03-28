"""Replayt boundary coverage for the LangGraph bridge.

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

from replayt_langgraph_bridge import compile_replayt_workflow, initial_bridge_state


def test_compile_requires_initial_state() -> None:
    """Bridge compile requires ``Workflow.set_initial`` (``workflow.initial_state`` contract)."""
    from replayt.workflow import Workflow

    wf = Workflow("t")
    wf.step("a")(lambda ctx: None)

    with pytest.raises(
        ValueError,
        match=r"set_initial",
    ):
        compile_replayt_workflow(wf)


def test_linear_workflow_via_langgraph(tmp_path: Path) -> None:
    """``RunContext.data`` mirrors ``context``; ``JSONLStore``/``Runner`` + ``MemorySaver`` invoke (CHECKPOINT_PERSISTENCE §6)."""
    from replayt.workflow import Workflow

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
    from replayt.workflow import Workflow

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
    assert out1["context"]["seed"] is True
    assert out1["context"]["phase"] == 1
    assert out1["replayt_next"] == "second"
    assert len(list(saver.list(cfg))) >= 1

    out2 = graph.invoke(None, config=cfg, context={"runner": runner})
    assert out2["context"]["phase"] == 11
    assert out2["replayt_next"] == ""
    assert out2["context"]["seed"] is True


def test_unknown_next_state_raises(tmp_path: Path) -> None:
    """Routing rejects unknown next step; ``MemorySaver`` present (CHECKPOINT_PERSISTENCE §6 baseline)."""
    from replayt.workflow import Workflow

    wf = Workflow("bad")

    @wf.step("a")
    def a(ctx):
        return "nonexistent"

    wf.set_initial("a")

    store = JSONLStore(tmp_path / "e.jsonl")
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())

    graph = compile_replayt_workflow(wf, checkpointer=MemorySaver())
    with pytest.raises(
        RuntimeError,
        match=r"unknown next state",
    ):
        graph.invoke(
            initial_bridge_state(),
            config={"configurable": {"thread_id": "t2"}},
            context={"runner": runner},
        )


def test_declared_edge_violation_raises(tmp_path: Path) -> None:
    """Declared-edge violation; ``MemorySaver`` present (CHECKPOINT_PERSISTENCE §6 baseline)."""
    from replayt.workflow import Workflow

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
    with pytest.raises(
        RuntimeError,
        match=r"undeclared transition",
    ):
        graph.invoke(
            initial_bridge_state(),
            config={"configurable": {"thread_id": "t3"}},
            context={"runner": runner},
        )
