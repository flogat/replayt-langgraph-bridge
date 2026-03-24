"""Security tests for threat model validation."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver
from replayt.persistence import JSONLStore
from replayt.runner import Runner

from replayt_langgraph_bridge import compile_replayt_workflow, initial_bridge_state


def test_sensitive_data_not_logged_in_errors(tmp_path: Path) -> None:
    """Verify that error messages don't leak full state (threat model mitigation)."""
    from replayt.workflow import Workflow

    wf = Workflow("sensitive")

    @wf.step("a")
    def a(ctx):
        # Simulate sensitive data in context
        ctx.set("api_key", "secret-key-123")
        ctx.set("user_pii", "sensitive@example.com")
        return "nonexistent"  # This will trigger an error

    wf.set_initial("a")

    store = JSONLStore(tmp_path / "sensitive.jsonl")
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())

    graph = compile_replayt_workflow(wf, checkpointer=MemorySaver())
    
    with pytest.raises(RuntimeError) as exc_info:
        graph.invoke(
            initial_bridge_state(context={"api_key": "secret-key-123", "user_pii": "sensitive@example.com"}),
            context={"runner": runner},
            config={"configurable": {"thread_id": "t1"}},
        )
    
    # Verify that error message doesn't contain the sensitive data
    error_msg = str(exc_info.value)
    assert "secret-key-123" not in error_msg
    assert "sensitive@example.com" not in error_msg
    # But should contain helpful debugging info
    assert "unknown next state" in error_msg
    assert "nonexistent" in error_msg


def test_context_shallow_merge_behavior(tmp_path: Path) -> None:
    """Verify that context is shallow-merged as documented in threat model."""
    from replayt.workflow import Workflow

    wf = Workflow("merge_test")

    @wf.step("step1")
    def step1(ctx):
        ctx.set("level1", {"nested": "value"})
        ctx.set("level2", "simple")
        return "step2"

    @wf.step("step2")
    def step2(ctx):
        # Verify shallow merge behavior
        assert ctx.get("level1") == {"nested": "value"}
        assert ctx.get("level2") == "simple"
        return None

    wf.set_initial("step1")
    wf.note_transition("step1", "step2")

    store = JSONLStore(tmp_path / "merge.jsonl")
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())

    graph = compile_replayt_workflow(wf, checkpointer=MemorySaver())
    out = graph.invoke(
        initial_bridge_state(context={"initial": "data"}),
        context={"runner": runner},
        config={"configurable": {"thread_id": "t1"}},
    )

    # Verify final state
    assert out["context"]["initial"] == "data"
    assert out["context"]["level1"] == {"nested": "value"}
    assert out["context"]["level2"] == "simple"


def test_no_secrets_in_state_by_default(tmp_path: Path) -> None:
    """Verify that the bridge doesn't add secrets to state."""
    from replayt.workflow import Workflow

    wf = Workflow("no_secrets")

    @wf.step("a")
    def a(ctx):
        # Don't add secrets to context
        ctx.set("public_data", "safe")
        return None

    wf.set_initial("a")

    store = JSONLStore(tmp_path / "no_secrets.jsonl")
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())

    graph = compile_replayt_workflow(wf, checkpointer=MemorySaver())
    out = graph.invoke(
        initial_bridge_state(),
        context={"runner": runner},
        config={"configurable": {"thread_id": "t1"}},
    )

    # Verify no unexpected secrets in output
    for key, value in out["context"].items():
        if isinstance(value, str):
            assert "secret" not in key.lower()
            assert "password" not in key.lower()
            assert "key" not in key.lower() or "public" in key.lower()


def test_checkpoint_state_isolation(tmp_path: Path) -> None:
    """Verify that different workflow instances don't share state."""
    from replayt.workflow import Workflow

    wf = Workflow("isolation")

    @wf.step("a")
    def a(ctx):
        ctx.set("instance_id", ctx.get("seed", "unknown"))
        return None

    wf.set_initial("a")

    store = JSONLStore(tmp_path / "isolation.jsonl")
    runner1 = Runner(wf, store)
    runner1.run_id = str(uuid.uuid4())
    runner2 = Runner(wf, store)
    runner2.run_id = str(uuid.uuid4())

    graph = compile_replayt_workflow(wf, checkpointer=MemorySaver())
    
    # First instance
    out1 = graph.invoke(
        initial_bridge_state(context={"seed": "instance1"}),
        context={"runner": runner1},
        config={"configurable": {"thread_id": "t1"}},
    )
    
    # Second instance with different thread_id
    out2 = graph.invoke(
        initial_bridge_state(context={"seed": "instance2"}),
        context={"runner": runner2},
        config={"configurable": {"thread_id": "t2"}},
    )

    # Verify state isolation
    assert out1["context"]["instance_id"] == "instance1"
    assert out2["context"]["instance_id"] == "instance2"
    assert out1["context"]["instance_id"] != out2["context"]["instance_id"]
