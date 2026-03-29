"""Large-graph compile advisory (GRAPH_CONSTRUCTION_ERRORS §4.3, once per process)."""

from __future__ import annotations

import warnings

import pytest
from replayt.workflow import Workflow

import replayt_langgraph_bridge.graph as graph_mod
from replayt_langgraph_bridge import BridgeLargeGraphWarning, compile_replayt_workflow


def _linear_workflow(n_steps: int) -> Workflow:
    """Chain s0 -> s1 -> ... -> s{n-1} with terminal None on the last handler."""
    wf = Workflow(f"large_linear_{n_steps}")
    for i in range(n_steps):
        name = f"s{i}"
        if i + 1 < n_steps:
            nxt: str | None = f"s{i + 1}"
        else:
            nxt = None

        def make_handler(target: str | None):
            def step(_ctx):
                return target

            return step

        wf.step(name)(make_handler(nxt))
    wf.set_initial("s0")
    for i in range(n_steps - 1):
        wf.note_transition(f"s{i}", f"s{i + 1}")
    return wf


@pytest.fixture(autouse=True)
def reset_large_graph_advisory_flag() -> None:
    """Process-global advisory state must not leak across tests."""
    graph_mod._large_graph_advisory_emitted = False
    yield
    graph_mod._large_graph_advisory_emitted = False


def test_no_warning_below_threshold() -> None:
    n = graph_mod._LARGE_GRAPH_STEP_THRESHOLD - 1
    wf = _linear_workflow(n)
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        compile_replayt_workflow(wf)
    large = [w for w in recorded if issubclass(w.category, BridgeLargeGraphWarning)]
    assert not large, "expected no BridgeLargeGraphWarning below threshold"


def test_warning_once_per_process_at_threshold() -> None:
    n = graph_mod._LARGE_GRAPH_STEP_THRESHOLD
    wf = _linear_workflow(n)
    with warnings.catch_warnings(record=True) as first:
        warnings.simplefilter("always")
        compile_replayt_workflow(wf)
    w1 = [w for w in first if issubclass(w.category, BridgeLargeGraphWarning)]
    assert len(w1) == 1
    assert "256" in str(w1[0].message) or "replayt-langgraph-bridge" in str(w1[0].message)

    with warnings.catch_warnings(record=True) as second:
        warnings.simplefilter("always")
        compile_replayt_workflow(wf)
    w2 = [w for w in second if issubclass(w.category, BridgeLargeGraphWarning)]
    assert not w2, "second compile in same process must not repeat the advisory"
