"""Contract tests for replayt 0.5 readiness docs (Mission Control 8c5e0a89 / BACKLOG_REPLAYT_05_READINESS)."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DRAFT = _REPO_ROOT / "docs" / "COMPATIBILITY_UPDATE_REPLAYT_05.md"
_BOUNDARY = _REPO_ROOT / "docs" / "REPLAYT_BOUNDARY_TESTS.md"
_BACKLOG = _REPO_ROOT / "docs" / "BACKLOG_REPLAYT_05_READINESS.md"


def test_replayt_05_draft_exists_and_links_normative_backlog() -> None:
    text = _DRAFT.read_text(encoding="utf-8")
    assert "BACKLOG_REPLAYT_05_READINESS.md" in text
    assert "https://pypi.org/project/replayt/" in text
    assert "## API inventory (R2)" in text
    assert "R4" in text and ("Green CI" in text or "blocker" in text.lower())


def test_replayt_05_draft_records_pin_hold_and_section_1_unchanged() -> None:
    text = _DRAFT.read_text(encoding="utf-8")
    assert "replayt>=0.4.0,<0.5" in text or ">=0.4.0,<0.5" in text
    assert "§1 unchanged" in text or "**§1 unchanged**" in text


def test_boundary_tests_related_documents_links_replayt_05_stack() -> None:
    text = _BOUNDARY.read_text(encoding="utf-8")
    assert "## Related documents" in text
    assert "BACKLOG_REPLAYT_05_READINESS.md" in text
    assert "COMPATIBILITY_UPDATE_REPLAYT_05.md" in text


def test_backlog_spec_links_compatibility_draft() -> None:
    text = _BACKLOG.read_text(encoding="utf-8")
    assert "COMPATIBILITY_UPDATE_REPLAYT_05.md" in text
