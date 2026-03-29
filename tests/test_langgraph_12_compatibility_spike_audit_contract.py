"""Contract tests for LangGraph 1.2.x spike maintainer note in DEPENDENCY_AUDIT (backlog ad68b829)."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AUDIT = _REPO_ROOT / "docs" / "DEPENDENCY_AUDIT.md"
_SPIKE_HEADING = "### LangGraph 1.2.x compatibility spike (backlog `ad68b829`)"


def _spike_section() -> str:
    text = _AUDIT.read_text(encoding="utf-8")
    assert _SPIKE_HEADING in text, "expected LangGraph 1.2 spike History subsection"
    start = text.index(_SPIKE_HEADING)
    # Next ### at column 0 after the heading (History sibling or Dependency Inventory)
    rest = text[start + len(_SPIKE_HEADING) :]
    next_hdr = rest.find("\n### ")
    if next_hdr == -1:
        return rest
    return rest[:next_hdr]


def test_spike_section_documents_upstream_versions_table() -> None:
    section = _spike_section()
    assert "#### Upstream versions exercised" in section
    assert "**langgraph**" in section and "**1.1.3**" in section
    assert "langgraph-checkpoint-sqlite" in section


def test_spike_section_covers_touchpoint_inventory() -> None:
    """LG12-A1: §2 areas appear in the maintainer note."""
    section = _spike_section()
    assert "#### §2 touchpoint inventory" in section
    assert "2.1" in section and "compile_replayt_workflow" in section
    assert "2.2" in section and "BridgeValidatingCheckpointSaver" in section
    assert "2.3" in section and "checkpoint.base" in section
    assert "2.4" in section and "invoke" in section


def test_spike_section_records_test_oracles_and_ci_trio() -> None:
    """LG12-A2 / LG12-A3: bridge_graph oracle + pytest/ruff/mypy signal."""
    section = _spike_section()
    assert "tests/test_bridge_graph.py" in section
    assert "tests/test_disk_checkpoint_sqlite_roundtrip.py" in section
    assert "#### Test signal" in section
    assert "`uv run pytest`" in section
    assert "`uv run ruff check src tests`" in section
    assert "`uv run mypy -p replayt_langgraph_bridge`" in section


def test_spike_section_states_shim_and_pin_policy() -> None:
    """§4.1 shim strategy + Pin / SemVer decision."""
    section = _spike_section()
    assert "#### Shim strategy" in section
    assert "#### Pin / SemVer decision" in section
    assert "Hold" in section
    assert "<1.2" in section
    assert "<1.3" in section
