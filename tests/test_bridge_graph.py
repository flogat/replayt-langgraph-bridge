from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver
from replayt.persistence import JSONLStore
from replayt.runner import Runner

from replayt_langgraph_bridge import compile_replayt_workflow, initial_bridge_state


def test_compile_requires_initial_state() -> None:
    from replayt.workflow import Workflow

    wf = Workflow("t")
    wf.step("a")(lambda ctx: None)

    with pytest.raises(ValueError, match="initial_state"):
        compile_replayt_workflow(wf)


def test_linear_workflow_via_langgraph(tmp_path: Path) -> None:
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
        context={"runner": runner},
        config={"configurable": {"thread_id": "t1"}},
    )

    assert out["context"]["seed"] is True
    assert out["context"]["n"] == 2
    assert out["replayt_next"] == ""


def test_unknown_next_state_raises(tmp_path: Path) -> None:
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
    with pytest.raises(RuntimeError, match="unknown next state"):
        graph.invoke(
            initial_bridge_state(),
            context={"runner": runner},
            config={"configurable": {"thread_id": "t2"}},
        )


def test_declared_edge_violation_raises(tmp_path: Path) -> None:
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
    with pytest.raises(RuntimeError, match="undeclared transition"):
        graph.invoke(
            initial_bridge_state(),
            context={"runner": runner},
            config={"configurable": {"thread_id": "t3"}},
        )
