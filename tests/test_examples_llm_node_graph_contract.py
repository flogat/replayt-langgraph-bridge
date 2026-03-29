"""Contract tests for ``examples/llm_node_graph.py`` (BACKLOG_FIRST_PARTY_LLM_SAMPLE §3.1, §3.6).

The example must not import ``[demo]``-only packages at module import time; see
**docs/REPLAYT_BOUNDARY_TESTS.md** §3.4.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from replayt_langgraph_bridge import compile_replayt_workflow

_REPO_ROOT = Path(__file__).resolve().parent.parent
_EXAMPLE = _REPO_ROOT / "examples" / "llm_node_graph.py"


def test_llm_node_graph_example_exists() -> None:
    assert _EXAMPLE.is_file(), "expected examples/llm_node_graph.py"


def test_llm_node_graph_source_contract() -> None:
    text = _EXAMPLE.read_text(encoding="utf-8")
    for needle in (
        "compile_replayt_workflow",
        "initial_bridge_state",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "LLM_PROVIDER",
        "LANGCHAIN_TRACING_V2",
        "not read",
        "if __name__",
        "vendor-metered",
        "LOG_REDACTION.md",
    ):
        assert needle in text, f"expected {needle!r} in examples/llm_node_graph.py"


def test_llm_node_graph_load_build_and_compile_without_demo_packages() -> None:
    """Importing the sample and compiling the graph must not require ``[demo]`` (default CI)."""
    spec = importlib.util.spec_from_file_location("_llm_node_graph_sample", _EXAMPLE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    wf = mod.build_demo_workflow()
    assert "call_llm" in wf.step_names()
    compile_replayt_workflow(wf)


@pytest.mark.parametrize(
    "forbidden",
    (
        "from langchain_openai",
        "from langchain_anthropic",
        "from langchain_core",
    ),
)
def test_llm_node_graph_no_demo_imports_at_top_level(forbidden: str) -> None:
    """Demo-only imports must stay inside callables (lazy), not at module scope."""
    lines: list[str] = []
    for line in _EXAMPLE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith("def ") or stripped.startswith("class "):
            break
        lines.append(stripped)
    body = "\n".join(lines)
    assert forbidden not in body, f"{forbidden} must not appear at module top level before first def"
