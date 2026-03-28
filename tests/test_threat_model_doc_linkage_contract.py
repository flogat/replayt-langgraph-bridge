"""THREAT_MODEL documentation linkage contract (filesystem reads only).

Guards **docs/THREAT_MODEL.md** title and section anchors plus **README.md** / **docs/MISSION.md** pointers per
**docs/REPLAYT_BOUNDARY_TESTS.md** §6 (not a replayt boundary test; no **replayt** import).
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_THREAT_MODEL = _REPO_ROOT / "docs" / "THREAT_MODEL.md"
_README = _REPO_ROOT / "README.md"
_MISSION = _REPO_ROOT / "docs" / "MISSION.md"

_TITLE_LINE = "# Threat Model: Checkpoint and State Data"
_REQUIRED_H2_HEADINGS = (
    "## 1. Assets",
    "## 2. Adversaries",
    "## 3. Trust Boundaries",
    "## 4. Mitigations",
    "## 5. Explicit Non-Goals",
    "## 6. Unsafe Fields",
    "## 7. Recommendations for Integrators",
    "## Links",
)


def test_threat_model_md_exists_at_docs_path() -> None:
    assert _THREAT_MODEL.is_file(), (
        "THREAT_MODEL doc linkage contract: missing docs/THREAT_MODEL.md (path relative to repository root)"
    )


def test_threat_model_md_first_line_is_title() -> None:
    """§6.2: stable title line for security reviewers and cross-links."""
    text = _THREAT_MODEL.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines, (
        "THREAT_MODEL doc linkage contract: docs/THREAT_MODEL.md is empty (expected title line)"
    )
    first = lines[0]
    assert first == _TITLE_LINE, (
        "THREAT_MODEL doc linkage contract: docs/THREAT_MODEL.md first line must be "
        f"{_TITLE_LINE!r}, got {first!r}"
    )


def test_threat_model_md_has_required_h2_headings_in_order() -> None:
    """§6.2: eight section headings in document order (sequential occurrence)."""
    body = _THREAT_MODEL.read_text(encoding="utf-8")
    pos = 0
    for heading in _REQUIRED_H2_HEADINGS:
        idx = body.find(heading, pos)
        assert idx != -1, (
            "THREAT_MODEL doc linkage contract: docs/THREAT_MODEL.md missing required heading "
            f"{heading!r} or it appears before a prior section (order must match spec)"
        )
        pos = idx + len(heading)


def test_readme_references_threat_model_md() -> None:
    text = _README.read_text(encoding="utf-8")
    assert "THREAT_MODEL.md" in text, (
        "THREAT_MODEL doc linkage contract: README.md must contain substring 'THREAT_MODEL.md'"
    )


def test_mission_references_threat_model_md() -> None:
    text = _MISSION.read_text(encoding="utf-8")
    assert "THREAT_MODEL.md" in text, (
        "THREAT_MODEL doc linkage contract: docs/MISSION.md must contain substring 'THREAT_MODEL.md'"
    )
