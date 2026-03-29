"""Contract tests for CHECKPOINT_PERSISTENCE two-persistence-planes section (backlog fae06d2c)."""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CHECKPOINT_DOC = _REPO_ROOT / "docs" / "CHECKPOINT_PERSISTENCE.md"
_README = _REPO_ROOT / "README.md"

_TWO_PLANES_HEADING = (
    "## Two persistence planes (LangGraph checkpointer vs replayt Runner / store)"
)
_ANCHOR_FRAGMENT = "two-persistence-planes-langgraph-checkpointer-vs-replayt-runner--store"


def test_checkpoint_persistence_two_planes_section_exists() -> None:
    text = _CHECKPOINT_DOC.read_text(encoding="utf-8")
    assert _TWO_PLANES_HEADING in text
    assert "```mermaid" in text
    assert "BridgeStateValidationError" in text
    assert "JSONLStore" in text


def test_checkpoint_persistence_failure_layers_mentioned() -> None:
    """Layer-grouped bullets: LangGraph saver, bridge validation, replayt store."""
    text = _CHECKPOINT_DOC.read_text(encoding="utf-8")
    start = text.index(_TWO_PLANES_HEADING)
    # Stop before next numbered major section (## 3.)
    end = text.index("\n## 3. In-memory vs durable checkpointers", start)
    section = text[start:end]
    assert "LangGraph checkpointer" in section or "serialized graph state" in section
    assert "Bridge inbound validation" in section
    assert "Replayt Runner" in section


def test_readme_links_two_persistence_planes_anchor() -> None:
    readme = _README.read_text(encoding="utf-8")
    assert _ANCHOR_FRAGMENT in readme
    assert re.search(
        r"\[two persistence planes \(replayt store vs LangGraph checkpointer\)\]",
        readme,
        re.IGNORECASE,
    ), "expected README anchor text for two persistence planes"
