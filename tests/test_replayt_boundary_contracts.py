"""Replayt boundary (consumer contract) tests without LangGraph.

Exercises supported ``replayt.*`` APIs the bridge depends on (``Workflow``, ``Runner``,
``RunContext`` data, persistence stores). Normative scope and assertion style:
``docs/REPLAYT_BOUNDARY_TESTS.md``.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import replayt
from replayt.persistence import JSONLStore
from replayt.runner import RunResult, Runner
from replayt.workflow import Workflow


def test_replayt_package_exposes_version_tuple() -> None:
    """Integrators and CI pin ``replayt``; the package should expose a parseable version tuple."""
    assert hasattr(replayt, "__version_tuple__"), (
        "replayt boundary: replayt package must expose __version_tuple__ for version checks"
    )


def test_runner_requires_set_initial(tmp_path: Path) -> None:
    """``Workflow.set_initial`` is required before ``Runner.run`` (``workflow.initial_state`` contract)."""
    wf = Workflow("no_initial")
    wf.step("a")(lambda ctx: None)
    store = JSONLStore(tmp_path / "run.jsonl")
    runner = Runner(wf, store)
    with pytest.raises(
        RuntimeError,
        match=r"set_initial",
    ):
        runner.run(run_id=str(uuid.uuid4()))


def test_linear_run_context_data_and_inputs(tmp_path: Path) -> None:
    """``RunContext.data`` carries ``Runner.run`` inputs and ``ctx.set`` across linear steps."""
    wf = Workflow("runner_linear")

    @wf.step("first")
    def first(ctx):
        assert ctx.get("seed") is True, (
            "replayt boundary: RunContext.data must include run inputs for the first step"
        )
        ctx.set("n", 1)
        return "second"

    @wf.step("second")
    def second(ctx):
        ctx.set("n", ctx.get("n", 0) + 1)
        return None

    wf.set_initial("first")
    wf.note_transition("first", "second")

    store = JSONLStore(tmp_path / "events.jsonl")
    runner = Runner(wf, store)
    result: RunResult = runner.run(
        inputs={"seed": True},
        run_id=str(uuid.uuid4()),
    )
    assert result.status == "completed", (
        "replayt boundary: linear workflow must complete when handler transitions match "
        "note_transition edges"
    )
    assert result.error is None, (
        "replayt boundary: completed runs must leave RunResult.error unset"
    )


def test_undeclared_transition_surfaces_in_run_result(tmp_path: Path) -> None:
    """``note_transition`` declares edges; handler return must match (undeclared transition contract)."""
    wf = Workflow("bad_edge")

    @wf.step("a")
    def a(ctx):
        return "b"

    @wf.step("b")
    def b(ctx):
        return None

    wf.set_initial("a")
    wf.note_transition("a", "c")

    store = JSONLStore(tmp_path / "e.jsonl")
    runner = Runner(wf, store)
    result = runner.run(run_id=str(uuid.uuid4()))
    assert result.status == "failed", (
        "replayt boundary: handler transition not covered by note_transition must fail the run"
    )
    assert result.error is not None, (
        "replayt boundary: failed runs must populate RunResult.error"
    )
    assert "undeclared transition" in result.error, (
        f"replayt boundary: expected 'undeclared transition' in error, got {result.error!r}"
    )


def test_unknown_step_return_surfaces_in_run_result(tmp_path: Path) -> None:
    """Handler return must name a registered step (step registry / routing contract)."""
    wf = Workflow("bad_next")

    @wf.step("a")
    def a(ctx):
        return "ghost"

    wf.set_initial("a")

    store = JSONLStore(tmp_path / "e.jsonl")
    runner = Runner(wf, store)
    result = runner.run(run_id=str(uuid.uuid4()))
    assert result.status == "failed", (
        "replayt boundary: unknown next step from handler must fail the run"
    )
    assert result.error is not None, (
        "replayt boundary: failed runs must populate RunResult.error"
    )
    assert "ghost" in result.error, (
        f"replayt boundary: RunResult.error should name the bad step; got {result.error!r}"
    )


def test_workflow_allows_transition_and_step_names_match_edges() -> None:
    """``Workflow.allows_transition`` and ``step_names`` match declared steps (bridge uses both)."""
    wf = Workflow("edges_api")

    @wf.step("a")
    def a(ctx):
        return "b"

    @wf.step("b")
    def b(ctx):
        return None

    wf.set_initial("a")
    wf.note_transition("a", "b")

    names = wf.step_names()
    assert set(names) == {"a", "b"}, (
        "replayt boundary: step_names must list every registered step"
    )
    assert wf.allows_transition("a", "b") is True, (
        "replayt boundary: allows_transition must permit declared a -> b edge"
    )
    assert wf.allows_transition("a", "c") is False, (
        "replayt boundary: allows_transition must reject undeclared a -> c edge"
    )
