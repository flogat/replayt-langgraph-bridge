"""Contract tests for root SECURITY.md vs **docs/SECURITY_REPORTING_SPEC.md** §2.1–§2.2.

Maps to product acceptance **SEC-1**, **SEC-3**, **SEC-4**, **SEC-5** (file-level checks); **SEC-2** is release-process
docs elsewhere.
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SECURITY = _REPO_ROOT / "SECURITY.md"

# §2.2 — phrases that must not appear as claims (substring scan; keep list aligned with spec).
_FORBIDDEN_SUBSTRINGS = (
    "SOC 2",
    "ISO 27001",
    "FIPS",
    "FedRAMP",
    "bug bounty",
    "paid support",
)


def test_security_md_exists_at_repository_root() -> None:
    assert _SECURITY.is_file(), "expected SECURITY.md at repository root (SECURITY_REPORTING_SPEC §2)"


def test_security_md_covers_reporting_and_private_disclosure() -> None:
    """§2.1 How to report + SEC-5 coordinated / private-first."""
    text = _SECURITY.read_text(encoding="utf-8")
    assert "private" in text.lower()
    assert "public" in text.lower() and "issue" in text.lower()
    assert "github.com/flogat/replayt-langgraph-bridge/security" in text


def test_security_md_covers_what_to_include_supported_versions_response_disclosure_scope() -> None:
    """§2.1 remaining table rows."""
    text = _SECURITY.read_text(encoding="utf-8")
    assert "What to include" in text
    assert "Supported versions" in text
    assert "pre-1.0" in text or "pre-1" in text
    assert "best-effort" in text.lower() or "best effort" in text.lower()
    assert "pyproject.toml" in text
    assert "Response expectations" in text
    assert "service-level" in text.lower() or "service level" in text.lower()
    assert "Disclosure" in text
    assert "Scope" in text
    assert "THREAT_MODEL.md" in text


def test_security_md_links_changelog_for_security_notes() -> None:
    """§2.3 / SEC-4 predictable release notes location."""
    text = _SECURITY.read_text(encoding="utf-8")
    assert "CHANGELOG.md" in text


def test_security_md_forbids_certification_and_bounty_claims() -> None:
    """§2.2 prohibitions (substring absence)."""
    text = _SECURITY.read_text(encoding="utf-8")
    lower = text.lower()
    for forbidden in _FORBIDDEN_SUBSTRINGS:
        assert forbidden.lower() not in lower, f"SECURITY.md must not claim or offer {forbidden!r} (§2.2)"
