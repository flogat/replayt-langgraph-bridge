"""Contract tests for release and changelog docs (docs/RELEASE_CHANGELOG.md §6 A–G, backlog acceptance)."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CHANGELOG = _REPO_ROOT / "CHANGELOG.md"
_RELEASE_SPEC = _REPO_ROOT / "docs" / "RELEASE_CHANGELOG.md"
_CONTRIBUTING = _REPO_ROOT / "CONTRIBUTING.md"
_README = _REPO_ROOT / "README.md"
_PYPROJECT = _REPO_ROOT / "pyproject.toml"
_DESIGN_PRINCIPLES = _REPO_ROOT / "docs" / "DESIGN_PRINCIPLES.md"


def test_changelog_exists_at_repo_root() -> None:
    assert _CHANGELOG.is_file()


def test_changelog_references_keep_a_changelog_and_semver() -> None:
    text = _CHANGELOG.read_text(encoding="utf-8")
    assert "keepachangelog.com" in text.lower()
    assert "semver.org" in text.lower()


def test_changelog_has_unreleased_section() -> None:
    text = _CHANGELOG.read_text(encoding="utf-8")
    assert "## [Unreleased]" in text


def test_changelog_has_dated_release_heading_matching_pyproject_version() -> None:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    version = data["project"]["version"]
    text = _CHANGELOG.read_text(encoding="utf-8")
    assert re.search(
        rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\s*$",
        text,
        re.MULTILINE,
    ), (
        f"expected dated ## [{version}] - YYYY-MM-DD in {_CHANGELOG} "
        "(docs/RELEASE_CHANGELOG.md §4 and §6 criterion A)"
    )


def test_release_changelog_spec_exists_under_docs() -> None:
    assert _RELEASE_SPEC.is_file()


def test_contributing_when_to_update_changelog_and_links_spec() -> None:
    text = _CONTRIBUTING.read_text(encoding="utf-8")
    assert "CHANGELOG.md" in text
    assert "docs/RELEASE_CHANGELOG.md" in text or "RELEASE_CHANGELOG.md" in text
    assert "user-visible" in text


def test_readme_points_to_changelog_and_release_spec() -> None:
    text = _README.read_text(encoding="utf-8")
    assert "CHANGELOG.md" in text
    assert "RELEASE_CHANGELOG.md" in text


def test_release_spec_covers_format_semver_initial_and_release_process() -> None:
    """§6(D): normative themes for §2–§5 (structure, SemVer, 0.1.0, manual release)."""
    text = _RELEASE_SPEC.read_text(encoding="utf-8")
    assert "Keep a Changelog" in text
    assert "Semantic Versioning" in text or "SemVer" in text
    assert "[Unreleased]" in text
    assert "0.1.0" in text
    assert "vX.Y.Z" in text
    assert "[project].version" in text
    assert "pyproject.toml" in text
    assert "PyPI" in text
    assert "Git tag" in text or "tag" in text.lower()


def test_release_spec_stays_linked_with_design_principles() -> None:
    """§6(D): cross-links between RELEASE_CHANGELOG and DESIGN_PRINCIPLES dependency/changelog bullets."""
    rel = _RELEASE_SPEC.read_text(encoding="utf-8")
    des = _DESIGN_PRINCIPLES.read_text(encoding="utf-8")
    assert "DESIGN_PRINCIPLES" in rel
    assert "RELEASE_CHANGELOG" in des


def test_release_spec_and_contributing_encode_pin_changelog_visibility() -> None:
    """§6(E): runtime constraint edits require Unreleased bullets; CONTRIBUTING repeats before → after."""
    rel = _RELEASE_SPEC.read_text(encoding="utf-8")
    con = _CONTRIBUTING.read_text(encoding="utf-8")
    assert "| E |" in rel
    assert "Pin drift" in rel
    assert "pyproject.toml" in rel
    assert "Unreleased" in rel
    assert "replayt" in rel
    assert "langgraph" in rel.lower()
    assert "requires-python" in rel
    assert "before → after" in rel
    assert "before → after" in con
    assert "**Dependency pins**" in con


def test_release_spec_encodes_breaking_changelog_lead_in() -> None:
    """§6(F): documented breaks use a Breaking lead-in (§2) for release review."""
    rel = _RELEASE_SPEC.read_text(encoding="utf-8")
    assert "| F |" in rel
    assert "**Breaking:**" in rel
    assert "Breaking" in rel


def test_release_spec_encodes_experimental_changelog_lead_in() -> None:
    """§6(G): experimental surface uses an Experimental lead-in; points at API.md."""
    rel = _RELEASE_SPEC.read_text(encoding="utf-8")
    assert "| G |" in rel
    assert "Experimental" in rel
    assert "API.md" in rel
